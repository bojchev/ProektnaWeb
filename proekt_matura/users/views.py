from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

from .models import CustomUser, UserProfile
from vault.models import Account
from budget.models import Income, Expense, Category
from invest.models import Portfolio, Holding, Transaction
from goals.models import Goal


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        first_name     = request.POST.get('first_name', '').strip()
        last_name      = request.POST.get('last_name', '').strip()
        username       = request.POST.get('username', '').strip()
        email          = request.POST.get('email', '').strip()
        password1      = request.POST.get('password1', '')
        password2      = request.POST.get('password2', '')
        risk_tolerance = request.POST.get('risk_tolerance', 'moderate')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'users/signup.html')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'users/signup.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'users/signup.html')

        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            password=password1,
            first_name=first_name,
            last_name=last_name,
        )
        UserProfile.objects.create(user=user, risk_tolerance=risk_tolerance)
        Portfolio.objects.create(user=user, cash_balance=Decimal('0.00'))

        login(request, user)
        return redirect('dashboard')

    return render(request, 'users/signup.html')


@login_required
def dashboard(request):
    user = request.user
    now  = timezone.localtime()

    hour = now.hour
    if hour < 12:
        time_of_day = 'morning'
    elif hour < 17:
        time_of_day = 'afternoon'
    else:
        time_of_day = 'evening'

    # ── Vault ──
    ASSET_TYPES     = ['checking', 'savings', 'cash']
    LIABILITY_TYPES = ['credit_card', 'loan', 'mortgage']
    accounts        = Account.objects.filter(user=user)
    vault_assets      = accounts.filter(account_type__in=ASSET_TYPES)
    vault_liabilities = accounts.filter(account_type__in=LIABILITY_TYPES)
    total_vault_cash  = sum(a.balance for a in vault_assets) or Decimal('0')
    total_debt        = sum(a.balance for a in vault_liabilities) or Decimal('0')

    # ── Budget ──
    incomes        = Income.objects.filter(user=user)
    expenses       = Expense.objects.filter(user=user)
    total_income   = sum(i.amount for i in incomes) or Decimal('0')
    total_expenses = sum(e.amount for e in expenses) or Decimal('0')
    budget_leftover = total_vault_cash + total_income - total_expenses

    suggested_investment = (
        budget_leftover * user.profile.suggested_invest_percentage / 100
        if budget_leftover > 0 else Decimal('0')
    )

    # Top 5 expense categories
    expense_categories = Category.objects.filter(user=user, category_type='expense')
    top_expense_categories = []
    for cat in expense_categories:
        amount = sum(e.amount for e in expenses.filter(category=cat))
        if amount > 0:
            top_expense_categories.append({
                'name': cat.name, 'amount': amount,
                'limit': amount, 'pct': 100,
            })
    top_expense_categories = sorted(top_expense_categories, key=lambda x: x['amount'], reverse=True)[:5]

    # Recent budget entries (combined)
    recent_inc = list(incomes.order_by('-date')[:5])
    recent_exp = list(expenses.order_by('-date')[:5])
    for e in recent_inc: e.entry_type = 'income'
    for e in recent_exp: e.entry_type = 'expense'
    recent_budget_entries = sorted(recent_inc + recent_exp, key=lambda x: x.date, reverse=True)[:5]

    # ── Invest ──
    try:
        portfolio    = Portfolio.objects.get(user=user)
        holdings     = list(Holding.objects.filter(portfolio=portfolio).select_related('security'))
        total_invested = sum(h.current_value for h in holdings) + portfolio.cash_balance
        portfolio_cash = portfolio.cash_balance
        top_holdings   = sorted(holdings, key=lambda h: h.current_value, reverse=True)[:5]
        recent_invest_transactions = Transaction.objects.filter(
            portfolio=portfolio
        ).select_related('security').order_by('-date')[:5]
    except Portfolio.DoesNotExist:
        total_invested = Decimal('0')
        portfolio_cash = Decimal('0')
        top_holdings   = []
        recent_invest_transactions = []

    # ── Net Worth ──
    net_worth = total_vault_cash - total_debt + total_invested

    # ── Goals ──
    goals           = Goal.objects.filter(user=user)
    completed_goals = [g for g in goals if g.is_completed]

    return render(request, 'dashboard.html', {
        'time_of_day': time_of_day,
        'today': now.strftime('%B %d, %Y'),
        'net_worth': net_worth,
        'total_vault_cash': total_vault_cash,
        'total_debt': total_debt,
        'total_invested': total_invested,
        'budget_leftover': budget_leftover,
        'suggested_investment': suggested_investment,
        'vault_assets': vault_assets,
        'vault_liabilities': vault_liabilities,
        'goals': goals,
        'completed_goals': completed_goals,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'top_expense_categories': top_expense_categories,
        'recent_budget_entries': recent_budget_entries,
        'top_holdings': top_holdings,
        'portfolio_cash': portfolio_cash,
        'recent_invest_transactions': recent_invest_transactions,
        'has_notifications': len(completed_goals) > 0,
    })


@login_required
def profile(request):
    if request.method == 'POST':
        user    = request.user
        prof = user.profile

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name  = request.POST.get('last_name', user.last_name)
        user.email      = request.POST.get('email', user.email)
        user.save()

        prof.risk_tolerance = request.POST.get('risk_tolerance', prof.risk_tolerance)
        custom_pct = request.POST.get('custom_invest_percentage', '').strip()
        prof.custom_invest_percentage = Decimal(custom_pct) if custom_pct else None
        prof.save()

        messages.success(request, 'Profile updated.')
        return redirect('dashboard')

    return render(request, 'dashboard.html')
