from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from decimal import Decimal

from .models import Income, Expense, Category
from vault.models import Account


@login_required
def index(request):
    from vault.models import Account

    user     = request.user
    incomes  = Income.objects.filter(user=user).select_related('category').order_by('-date')
    expenses = Expense.objects.filter(user=user).select_related('category').order_by('-date')

    total_income   = sum(i.amount for i in incomes) or Decimal('0')
    total_expenses = sum(e.amount for e in expenses) or Decimal('0')

    vault_cash = sum(
        a.balance for a in Account.objects.filter(user=user, account_type__in=['checking', 'savings', 'cash'])
    ) or Decimal('0')

    budget_leftover = vault_cash + total_income - total_expenses
    suggested_investment = (
        budget_leftover * user.profile.suggested_invest_percentage / Decimal('100')
        if budget_leftover > 0 else Decimal('0')
    )

    expense_ratio = int(total_expenses / total_income * 100) if total_income > 0 else 0


    inc_list = list(incomes)
    exp_list = list(expenses)
    for e in inc_list: e.entry_type = 'income'
    for e in exp_list: e.entry_type = 'expense'
    entries = sorted(inc_list + exp_list, key=lambda x: x.date, reverse=True)


    exp_categories_qs = Category.objects.filter(user=user, category_type='expense')
    expense_categories = []
    for cat in exp_categories_qs:
        total = sum(e.amount for e in expenses.filter(category=cat)) or Decimal('0')
        expense_categories.append({'name': cat.name, 'total': total, 'share_pct': 0})
    grand = sum(c['total'] for c in expense_categories) or Decimal('1')
    for cat in expense_categories:
        cat['share_pct'] = int(cat['total'] / grand * 100)
    expense_categories = sorted(expense_categories, key=lambda x: x['total'], reverse=True)


    inc_categories_qs = Category.objects.filter(user=user, category_type='income')
    income_categories = []
    for cat in inc_categories_qs:
        cat_incomes = incomes.filter(category=cat)
        total = sum(i.amount for i in cat_incomes) or Decimal('0')
        income_categories.append({'name': cat.name, 'total': total, 'count': cat_incomes.count()})

    all_cats    = Category.objects.filter(user=user)
    inc_choices = Category.objects.filter(user=user, category_type='income')
    exp_choices = Category.objects.filter(user=user, category_type='expense')
    accounts = Account.objects.filter(user=user)

    return render(request, 'budget/budget.html', {
        'entries': entries,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'budget_leftover': budget_leftover,
        'suggested_investment': suggested_investment,
        'income_count': incomes.count(),
        'expense_count': expenses.count(),
        'expense_ratio': min(expense_ratio, 100),
        'expense_categories': expense_categories,
        'income_categories': income_categories,
        'all_category_choices': all_cats,
        'income_category_choices': inc_choices,
        'expense_category_choices': exp_choices,
        'account_choices': accounts,
    })


@login_required
def add_entry(request):
    if request.method == 'POST':
        entry_type  = request.POST.get('entry_type', 'income')
        description = request.POST['description']
        amount      = Decimal(request.POST['amount'])
        date        = request.POST['date']
        notes       = request.POST.get('notes', '')
        category_id = request.POST.get('category')
        category    = Category.objects.filter(pk=category_id, user=request.user).first()
        account_id  = request.POST.get('account')
        account     = Account.objects.filter(pk=account_id, user=request.user).first() if account_id else None

        if entry_type == 'income':
            Income.objects.create(
                user=request.user, description=description,
                amount=amount, date=date, category=category, notes=notes, account=account,
            )
            if account:
                account.balance += amount
                account.save()
        else:
            Expense.objects.create(
                user=request.user, description=description,
                amount=amount, date=date, category=category, notes=notes, account=account,
            )
            if account:
                account.balance -= amount
                account.save()
    return redirect('budget:index')


@login_required
def edit_entry(request, pk):
    if request.method == 'POST':
        description = request.POST['description']
        amount      = Decimal(request.POST['amount'])
        date        = request.POST['date']
        category_id = request.POST.get('category')
        category    = Category.objects.filter(pk=category_id, user=request.user).first()
        account_id  = request.POST.get('account')
        new_account = Account.objects.filter(pk=account_id, user=request.user).first() if account_id else None

        entry = Income.objects.filter(pk=pk, user=request.user).first()
        if not entry:
            entry = get_object_or_404(Expense, pk=pk, user=request.user)

        # adjust balances: remove old effect then apply new
        old_amount = entry.amount
        old_account = getattr(entry, 'account', None)
        # reverse old impact
        if isinstance(entry, Income):
            if old_account:
                old_account.balance -= old_amount
                old_account.save()
        else:
            if old_account:
                old_account.balance += old_amount
                old_account.save()

        # apply new values
        entry.description = description
        entry.amount      = amount
        entry.date        = date
        if category:
            entry.category = category
        entry.account = new_account
        entry.save()

        if isinstance(entry, Income):
            if new_account:
                new_account.balance += amount
                new_account.save()
        else:
            if new_account:
                new_account.balance -= amount
                new_account.save()
    return redirect('budget:index')


@login_required
def delete_entry(request, pk):
    if request.method == 'POST':
        entry = Income.objects.filter(pk=pk, user=request.user).first()
        if not entry:
            entry = Expense.objects.filter(pk=pk, user=request.user).first()
        if entry:
            # reverse balance impact
            acct = getattr(entry, 'account', None)
            if isinstance(entry, Income):
                if acct:
                    acct.balance -= entry.amount
                    acct.save()
            else:
                if acct:
                    acct.balance += entry.amount
                    acct.save()
            entry.delete()
    return redirect('budget:index')


@login_required
def add_category(request):
    if request.method == 'POST':
        Category.objects.create(
            user=request.user,
            name=request.POST['name'],
            category_type=request.POST.get('category_type', 'expense'),
        )
    return redirect('budget:index')


@login_required
def invest_now(request):
    from vault.models import Account
    from invest.models import Portfolio, Transaction

    if request.method == 'POST':
        user = request.user

        vault_cash = sum(
            a.balance for a in Account.objects.filter(user=user, account_type__in=['checking', 'savings', 'cash'])
        ) or Decimal('0')

        incomes        = Income.objects.filter(user=user)
        expenses       = Expense.objects.filter(user=user)
        total_income   = sum(i.amount for i in incomes) or Decimal('0')
        total_expenses = sum(e.amount for e in expenses) or Decimal('0')

        budget_leftover = vault_cash + total_income - total_expenses
        amount = budget_leftover * user.profile.suggested_invest_percentage / Decimal('100')

        if amount > 0:

            invest_category, _ = Category.objects.get_or_create(
                user=user,
                name='Investment',
                category_type='expense',
                defaults={'is_preset': False},
            )
            Expense.objects.create(
                user=user,
                category=invest_category,
                description=f'Investment deposit (auto)',
                amount=amount,
                date=timezone.now().date(),
                notes='Automatically created by Invest Now',
            )


            portfolio, _ = Portfolio.objects.get_or_create(
                user=user, defaults={'cash_balance': Decimal('0')}
            )
            portfolio.cash_balance += amount
            portfolio.save()

            Transaction.objects.create(
                portfolio=portfolio,
                security=None,
                transaction_type='deposit',
                quantity=None,
                price=amount,
                date=timezone.now().date(),
                from_budget=True,
            )
    return redirect('budget:index')
