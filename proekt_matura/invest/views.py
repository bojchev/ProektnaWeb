from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from decimal import Decimal
import json

from .models import Portfolio, Security, Holding, Transaction


def _get_allocation(holdings, portfolio_cash):
    totals = {}
    COLORS = {
        'stock': '#7297c5', 'crypto': '#e65100', 'bond': '#2e7d32',
        'investment_fund': '#6a1b9a', 'pension_fund': '#880e4f', 'bank_deposit': '#0d47a1',
    }
    LABELS = {
        'stock': 'Stocks', 'crypto': 'Crypto', 'bond': 'Bonds',
        'investment_fund': 'Funds', 'pension_fund': 'Pension', 'bank_deposit': 'Deposits',
    }
    for h in holdings:
        t = h.security.asset_type
        totals[t] = totals.get(t, Decimal('0')) + h.current_value

    total_all = sum(totals.values()) + portfolio_cash
    if total_all == 0:
        total_all = Decimal('1')
    allocation = [
        {
            'type': t, 'label': LABELS.get(t, t),
            'value': v, 'pct': v / total_all * 100,
            'color': COLORS.get(t, '#999'),
        }
        for t, v in sorted(totals.items(), key=lambda x: x[1], reverse=True)
    ]
    cash_pct = portfolio_cash / total_all * 100
    return allocation, cash_pct


@login_required
def index(request):
    user      = request.user
    portfolio, _ = Portfolio.objects.get_or_create(user=user, defaults={'cash_balance': Decimal('0')})
    holdings  = list(Holding.objects.filter(portfolio=portfolio).select_related('security'))

    total_value   = sum(h.current_value for h in holdings) + portfolio.cash_balance
    total_cost    = sum(h.total_cost_basis for h in holdings)
    total_gain    = sum(h.gain for h in holdings) if holdings else Decimal('0')
    portfolio_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else Decimal('0')

    recent_tx = Transaction.objects.filter(portfolio=portfolio).select_related('security').order_by('-date')
    last_tx   = recent_tx.first()

    allocation, cash_pct = _get_allocation(holdings, portfolio.cash_balance)

    return render(request, 'invest/invest.html', {
        'portfolio': portfolio,
        'holdings': holdings,
        'portfolio_total': total_value,
        'portfolio_cash': portfolio.cash_balance,
        'portfolio_gain_pct': portfolio_gain_pct,
        'holding_count': len(holdings),
        'total_gain': total_gain,
        'last_tx_date': last_tx.date if last_tx else '—',
        'last_tx_type': last_tx.get_transaction_type_display() if last_tx else '—',
        'last_tx_ticker': last_tx.security.ticker if last_tx and last_tx.security else '—',
        'allocation': allocation,
        'cash_pct': cash_pct,
        'recent_transactions': recent_tx[:10],
    })


@login_required
def buy(request):
    if request.method == 'POST':
        portfolio, _ = Portfolio.objects.get_or_create(
            user=request.user, defaults={'cash_balance': Decimal('0')}
        )
        ticker    = request.POST['ticker'].upper()
        name      = request.POST.get('name', ticker)
        asset_type = request.POST.get('asset_type', 'stock')
        quantity  = Decimal(request.POST['quantity'])
        price     = Decimal(request.POST['price'])
        date      = request.POST['date']
        manual    = request.POST.get('requires_manual_tracking') == 'true'

        total_cost = quantity * price

        # Check sufficient uninvested cash
        if total_cost > portfolio.cash_balance:
            max_qty = int(portfolio.cash_balance / price) if price > 0 else 0
            messages.error(
                request,
                f'Insufficient cash. You need ${total_cost:.2f} but only have '
                f'${portfolio.cash_balance:.2f} available. '
                f'Max you can buy: {max_qty} units.'
            )
            return redirect('invest:index')

        security, created = Security.objects.get_or_create(
            ticker=ticker,
            defaults={
                'name': name, 'asset_type': asset_type,
                'current_price': price, 'requires_manual_tracking': manual,
            }
        )
        if not created:
            security.current_price = price
            security.save()

        holding, created = Holding.objects.get_or_create(
            portfolio=portfolio, security=security,
            defaults={'quantity': Decimal('0'), 'average_cost': Decimal('0')}
        )
        # Update average cost
        old_cost = holding.quantity * holding.average_cost
        new_cost = quantity * price
        new_total_qty = holding.quantity + quantity
        if new_total_qty > 0:
            holding.average_cost = (old_cost + new_cost) / new_total_qty
        holding.quantity = new_total_qty
        holding.save()

        # Deduct cost from uninvested cash
        portfolio.cash_balance -= total_cost
        portfolio.save()

        Transaction.objects.create(
            portfolio=portfolio, security=security, transaction_type='buy',
            quantity=quantity, price=price, date=date, from_budget=False,
        )
        messages.success(request, f'Bought {quantity} units of {ticker} for ${total_cost:.2f}.')
    return redirect('invest:index')


@login_required
def sell(request, pk):
    holding = get_object_or_404(Holding, pk=pk, portfolio__user=request.user)
    if request.method == 'POST':
        quantity = Decimal(request.POST['quantity'])
        price    = Decimal(request.POST['price'])
        date     = request.POST['date']

        proceeds = quantity * price
        holding.portfolio.cash_balance += proceeds
        holding.portfolio.save()

        holding.quantity -= quantity
        if holding.quantity <= 0:
            holding.delete()
        else:
            holding.save()

        Transaction.objects.create(
            portfolio=holding.portfolio, security=holding.security, transaction_type='sell',
            quantity=quantity, price=price, date=date, from_budget=False,
        )
    return redirect('invest:index')


@login_required
def deposit(request):
    if request.method == 'POST':
        portfolio, _ = Portfolio.objects.get_or_create(
            user=request.user, defaults={'cash_balance': Decimal('0')}
        )
        amount = Decimal(request.POST['amount'])
        date   = request.POST['date']
        portfolio.cash_balance += amount
        portfolio.save()
        Transaction.objects.create(
            portfolio=portfolio, security=None, transaction_type='deposit',
            quantity=None, price=amount, date=date, from_budget=False,
        )
    return redirect('invest:index')


@login_required
def withdraw(request):
    if request.method == 'POST':
        portfolio = get_object_or_404(Portfolio, user=request.user)
        amount    = Decimal(request.POST['amount'])
        date      = request.POST['date']
        if amount <= portfolio.cash_balance:
            portfolio.cash_balance -= amount
            portfolio.save()
            Transaction.objects.create(
                portfolio=portfolio, security=None, transaction_type='withdraw',
                quantity=None, price=amount, date=date, from_budget=False,
            )
    return redirect('invest:index')


@login_required
def update_price(request, pk):
    security = get_object_or_404(Security, pk=pk)
    if request.method == 'POST':
        security.current_price = Decimal(request.POST['price'])
        security.save()
    return redirect('invest:index')


@login_required
def transactions(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    txs = Transaction.objects.filter(portfolio=portfolio).select_related('security').order_by('-date')
    return render(request, 'invest/transactions.html', {'transactions': txs})


@login_required
def search_securities(request):
    """Search Yahoo Finance for securities by ticker or company name."""
    query = request.GET.get('q', '').strip()
    if not query or len(query) < 1:
        return JsonResponse({'results': []})

    try:
        import requests as req

        # Use Yahoo Finance's public autocomplete/search endpoint
        url = 'https://query2.finance.yahoo.com/v1/finance/search'
        params = {
            'q': query,
            'quotesCount': 10,
            'newsCount': 0,
            'listsCount': 0,
            'enableFuzzyQuery': True,
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = req.get(url, params=params, headers=headers, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for quote in data.get('quotes', []):
            # Skip non-equity/crypto/ETF results (e.g. futures, options, currencies)
            quote_type = quote.get('quoteType', '').upper()
            if quote_type not in ('EQUITY', 'ETF', 'MUTUALFUND', 'CRYPTOCURRENCY', 'INDEX'):
                continue

            # Map Yahoo quoteType to our asset_type
            if quote_type == 'CRYPTOCURRENCY':
                asset_type = 'crypto'
            elif quote_type in ('ETF', 'MUTUALFUND'):
                asset_type = 'investment_fund'
            else:
                asset_type = 'stock'

            results.append({
                'ticker': quote.get('symbol', ''),
                'name': quote.get('shortname') or quote.get('longname') or quote.get('symbol', ''),
                'price': 0,  # Price is fetched separately when user selects a result
                'exchange': quote.get('exchange', ''),
                'type': asset_type,
            })

        # If we got results, try to fetch the price for the first result using yfinance
        if results:
            try:
                import yfinance as yf
                first_ticker = yf.Ticker(results[0]['ticker'])
                info = first_ticker.info or {}
                price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
                if price:
                    results[0]['price'] = float(price)
            except Exception:
                pass  # Price fetch is best-effort

        return JsonResponse({'results': results})
    except Exception:
        return JsonResponse({'results': []})


def _guess_asset_type(info):
    """Guess asset type from yfinance info."""
    quote_type = info.get('quoteType', '').lower()
    if quote_type == 'cryptocurrency':
        return 'crypto'
    if quote_type == 'etf' or quote_type == 'mutualfund':
        return 'investment_fund'
    return 'stock'


@login_required
def fetch_price(request):
    """Fetch current price for a ticker from Yahoo Finance."""
    ticker = request.GET.get('ticker', '').strip().upper()
    if not ticker:
        return JsonResponse({'error': 'No ticker provided'}, status=400)

    try:
        import yfinance as yf
        t = yf.Ticker(ticker)
        info = t.info
        price = info.get('currentPrice') or info.get('regularMarketPrice') or info.get('previousClose')
        if price:
            return JsonResponse({
                'ticker': ticker,
                'price': float(price),
                'name': info.get('shortName') or info.get('longName') or ticker,
            })
        return JsonResponse({'error': 'Price not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
