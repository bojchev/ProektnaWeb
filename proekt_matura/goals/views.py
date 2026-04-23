from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from decimal import Decimal

from .models import Goal, GoalContribution
from vault.models import Account


@login_required
def index(request):
    goals = Goal.objects.filter(user=request.user).prefetch_related('contributions')
    from vault.models import Account
    accounts = Account.objects.filter(user=request.user)

    total_goals       = goals.count()
    completed_count   = sum(1 for g in goals if g.is_completed)
    total_contributed = sum(g.total_contributed for g in goals) or Decimal('0')
    total_target      = sum(g.target_amount for g in goals) or Decimal('0')
    total_remaining   = sum(g.remaining for g in goals) or Decimal('0')
    overall_progress  = (total_contributed / total_target * 100) if total_target > 0 else 0
    completed_goals   = [g for g in goals if g.is_completed]

    return render(request, 'goals/goals.html', {
        'goals': goals,
        'total_goals': total_goals,
        'completed_count': completed_count,
        'total_contributed': total_contributed,
        'total_target': total_target,
        'total_remaining': total_remaining,
        'overall_progress': overall_progress,
        'completed_goals': completed_goals,
        'accounts': accounts,
    })


@login_required
def add_goal(request):
    if request.method == 'POST':
        Goal.objects.create(
            user=request.user,
            name=request.POST['name'],
            target_amount=Decimal(request.POST['target_amount']),
            target_date=request.POST['target_date'],
            notes=request.POST.get('notes', ''),
        )
    return redirect('goals:index')


@login_required
def contribute(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        amount = Decimal(request.POST['amount'])
        account_id = request.POST.get('account')
        account = Account.objects.filter(pk=account_id, user=request.user).first() if account_id else None

        # deduct from chosen account balance if provided and has funds
        if account:
            # ensure sufficient funds for asset accounts
            if not account.is_liability and account.balance < amount:
                messages.error(request, 'Insufficient funds in selected account.')
                return redirect('goals:index')

            if account.is_liability:
                # paying into a goal from a liability increases the liability balance
                account.balance += amount
            else:
                # reduce asset account
                account.balance -= amount
            account.save()

        GoalContribution.objects.create(
            goal=goal,
            account=account,
            amount=amount,
            date=request.POST['date'],
            notes=request.POST.get('notes', ''),
        )
        messages.success(request, 'Contribution logged.')
    return redirect('goals:index')


@login_required
def edit_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.name          = request.POST['name']
        goal.target_amount = Decimal(request.POST['target_amount'])
        goal.target_date   = request.POST['target_date']
        goal.save()
    return redirect('goals:index')


@login_required
def delete_goal(request, pk):
    goal = get_object_or_404(Goal, pk=pk, user=request.user)
    if request.method == 'POST':
        goal.delete()
    return redirect('goals:index')
