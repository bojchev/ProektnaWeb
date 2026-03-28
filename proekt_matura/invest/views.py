from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal

from .models import Portfolio, Security, Holding, Transaction


def _get_allocation(holdings, portfolio_cash):
    totals = {}
    COLORS = {
        'stock': '#7297c5', 'crypto': '#e65100', 'bond': '#2e7d32',
        'fund': '#6a1b9a', 'pension': '#880e4f', 'deposit': '#0d47a1',
    }
    LABELS = {
        'stock': 'Stocks', 'crypto': 'Crypto', 'bond': 'Bonds',
        'fund': 'Funds', 'pension': 'Pension', 'deposit': 'Deposits',
    }
    for h in holdings:
        t = h.security.asset_type
        totals[t] = totals.get(t, Decimal('0')) + h.current_value

    total_all = sum(totals.values()) + portfolio_cash or Decimal('1')
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
    total_cost    = sum(h.quantity * h.security.current_price for h in holdings)
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
        'last_tx_type': last_tx.tx_type if last_tx else '—',
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
        name      = request.POST['name']
        asset_type = request.POST.get('asset_type', 'stock')
        quantity  = Decimal(request.POST['quantity'])
        price     = Decimal(request.POST['price'])
        date      = request.POST['date']
        manual    = request.POST.get('requires_manual_tracking') == 'true'

        security, _ = Security.objects.get_or_create(
            ticker=ticker,
            defaults={
                'name': name, 'asset_type': asset_type,
                'current_price': price, 'requires_manual_tracking': manual,
            }
        )
        security.current_price = price
        security.save()

        holding, _ = Holding.objects.get_or_create(
            portfolio=portfolio, security=security,
            defaults={'quantity': Decimal('0')}
        )
        holding.quantity += quantity
        holding.save()

        Transaction.objects.create(
            portfolio=portfolio, security=security, tx_type='BUY',
            quantity=quantity, price=price, date=date, from_budget=False,
        )
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
            portfolio=holding.portfolio, security=holding.security, tx_type='SELL',
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
            portfolio=portfolio, security=None, tx_type='DEPOSIT',
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
                portfolio=portfolio, security=None, tx_type='WITHDRAW',
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
