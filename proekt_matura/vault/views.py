from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from decimal import Decimal

from .models import Account


@login_required
def index(request):
    accounts = Account.objects.filter(user=request.user)

    ASSET_TYPES     = ['checking', 'savings', 'cash']
    LIABILITY_TYPES = ['credit_card', 'loan', 'mortgage']

    vault_assets      = accounts.filter(account_type__in=ASSET_TYPES)
    vault_liabilities = accounts.filter(account_type__in=LIABILITY_TYPES)

    total_assets = sum(a.balance for a in vault_assets) or Decimal('0')
    total_debt   = sum(a.balance for a in vault_liabilities) or Decimal('0')
    net_position = total_assets - total_debt

    return render(request, 'vault/vault.html', {
        'net_position': net_position,
        'total_assets': total_assets,
        'total_debt': total_debt,
        'asset_count': vault_assets.count(),
        'liability_count': vault_liabilities.count(),
        'checking_accounts':    accounts.filter(account_type='checking'),
        'savings_accounts':     accounts.filter(account_type='savings'),
        'cash_accounts':        accounts.filter(account_type='cash'),
        'credit_card_accounts': accounts.filter(account_type='credit_card'),
        'loan_accounts':        accounts.filter(account_type='loan'),
        'mortgage_accounts':    accounts.filter(account_type='mortgage'),
    })


@login_required
def add_account(request):
    if request.method == 'POST':
        interest_rate = request.POST.get('interest_rate') or None
        credit_limit  = request.POST.get('credit_limit') or None

        Account.objects.create(
            user=request.user,
            name=request.POST['name'],
            account_type=request.POST['account_type'],
            balance=Decimal(request.POST['balance']),
            interest_rate=Decimal(interest_rate) if interest_rate else None,
            credit_limit=Decimal(credit_limit) if credit_limit else None,
        )
    return redirect('vault:index')


@login_required
def edit_account(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        account.name    = request.POST['name']
        account.balance = Decimal(request.POST['balance'])
        ir = request.POST.get('interest_rate') or None
        cl = request.POST.get('credit_limit') or None
        account.interest_rate = Decimal(ir) if ir else None
        account.credit_limit  = Decimal(cl) if cl else None
        account.save()
    return redirect('vault:index')


@login_required
def delete_account(request, pk):
    account = get_object_or_404(Account, pk=pk, user=request.user)
    if request.method == 'POST':
        account.delete()
    return redirect('vault:index')
