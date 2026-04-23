from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from django.core.management.base import BaseCommand

from invest.models import Security


class Command(BaseCommand):
    help = 'Update current_price for Securities using Yahoo Finance (yfinance + fallback).'

    def add_arguments(self, parser):
        parser.add_argument('--tickers', nargs='+', help='Specific tickers to update (optional)')
        parser.add_argument('--workers', type=int, default=6, help='Number of parallel workers')
        parser.add_argument('--dry-run', action='store_true', help='Do not persist changes; just report')

    def handle(self, *args, **options):
        tickers_filter = options.get('tickers')
        workers = options.get('workers') or 6
        dry_run = options.get('dry_run')

        qs = Security.objects.filter(requires_manual_tracking=False).exclude(ticker__isnull=True).exclude(ticker__exact='')
        if tickers_filter:
            qs = qs.filter(ticker__in=tickers_filter)

        secs = list(qs)
        if not secs:
            self.stdout.write('No securities to update.')
            return

        # Map ticker -> list of Security objects (in case duplicates exist)
        ticker_map = {}
        for s in secs:
            t = s.ticker.strip().upper()
            if not t:
                continue
            ticker_map.setdefault(t, []).append(s)

        tickers = list(ticker_map.keys())
        self.stdout.write(f'Updating {len(tickers)} tickers using {workers} workers...')

        try:
            import yfinance as yf
        except Exception:
            yf = None

        import requests

        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Vaultly/1.0; +https://example.com)'
        }

        def fetch_price(ticker):
            # Try yfinance fast_info
            if yf:
                try:
                    t = yf.Ticker(ticker)
                    fast = getattr(t, 'fast_info', None)
                    if fast and getattr(fast, 'last_price', None):
                        return float(fast.last_price)
                    info = t.info or {}
                    price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                    if price:
                        return float(price)
                except Exception:
                    # continue to fallback
                    pass

            # Fallback to Yahoo chart endpoint
            try:
                url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker}'
                resp = requests.get(url, params={'range': '1d', 'interval': '1d'}, headers=headers, timeout=8)
                if resp.status_code == 200:
                    data = resp.json()
                    meta = data.get('chart', {}).get('result', [{}])[0].get('meta', {})
                    price = meta.get('regularMarketPrice') or meta.get('previousClose')
                    if price:
                        return float(price)
            except Exception:
                pass

            return None

        start_time = time.time()
        updated = 0
        failed = []

        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(fetch_price, t): t for t in tickers}
            for fut in as_completed(futures):
                t = futures[fut]
                try:
                    price = fut.result()
                except Exception as e:
                    failed.append((t, str(e)))
                    self.stderr.write(f'Error fetching {t}: {e}')
                    continue

                if price is None:
                    failed.append((t, 'no price found'))
                    self.stdout.write(f'No price for {t}')
                    continue

                syms = ticker_map.get(t, [])
                for s in syms:
                    old = s.current_price
                    if dry_run:
                        self.stdout.write(f'{s.ticker}: {old} -> {price}')
                    else:
                        s.current_price = Decimal(str(price))
                        try:
                            s.save(update_fields=['current_price'])
                            updated += 1
                            self.stdout.write(f'Updated {s.ticker}: {old} -> {s.current_price}')
                        except Exception as e:
                            failed.append((t, str(e)))
                            self.stderr.write(f'Failed saving {s.ticker}: {e}')

        elapsed = time.time() - start_time
        self.stdout.write(f'Done. Updated: {updated}. Failed: {len(failed)}. Time: {elapsed:.1f}s')
        if failed:
            self.stdout.write('Failures:')
            for f in failed[:20]:
                self.stdout.write(f' - {f[0]}: {f[1]}')
