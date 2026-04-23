from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from decimal import Decimal

from .models import Account
from .models import Transfer


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


@login_required
def transfer(request):
    if request.method == 'POST':
        from_id = request.POST.get('from_account')
        to_id = request.POST.get('to_account')
        amount = Decimal(request.POST.get('amount') or '0')
        date = request.POST.get('date')
        notes = request.POST.get('notes', '')

        from_acc = Account.objects.filter(pk=from_id, user=request.user).first()
        to_acc = Account.objects.filter(pk=to_id, user=request.user).first()

        # Basic validation and user feedback
        if not from_acc or not to_acc:
            messages.error(request, 'Please select valid source and destination accounts.')
            return redirect('vault:index')

        if from_acc == to_acc:
            messages.error(request, 'Source and destination accounts must be different.')
            return redirect('vault:index')

        if amount <= 0:
            messages.error(request, 'Transfer amount must be a positive number.')
            return redirect('vault:index')

        # If the source is an asset, ensure sufficient funds.
        if not from_acc.is_liability and from_acc.balance < amount:
            messages.error(request, 'Insufficient funds in the source account.')
            return redirect('vault:index')

        # perform transfer
        from_acc.balance -= amount
        to_acc.balance += amount
        from_acc.save()
        to_acc.save()
        Transfer.objects.create(from_account=from_acc, to_account=to_acc, amount=amount, date=date, notes=notes)
        messages.success(request, 'Transfer completed successfully.')
    return redirect('vault:index')
