from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.forms import inlineformset_factory
from .models import *
from .forms import *
from .filters import OrderFilter
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .decoraters import *



@unauthenticated_user
def registerPage(request):

    form = CreateUserForm()

    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user=form.save()
            username = form.cleaned_data.get('username')
            email= form.cleaned_data.get('email')
            phone=form.cleaned_data.get('phone')

            group = Group.objects.get(name='customer')
            user.groups.add(group)
            Customer.objects.create(user=user, name=username,email=email,phone=phone)

            messages.success(request, 'Succesfully created ' + username)
            return redirect('login')

    context = {'form': form}
    return render(request, 'accounts/register.html', context)

@unauthenticated_user
def loginPage(request):


    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.info(request, 'Username OR password is incorrect')

    context = {}
    return render(request, 'accounts/login.html', context)


@login_required(login_url='login')
@allowed_user(allowed_roles=['customer'])
def userPage(request):
    orders = request.user.customer.order_set.all()

    total_orders = orders.count()
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    ofdelivery = orders.filter(status='Out for delivery').count()
    print('ORDERS:', orders)

    context = {'orders': orders, 'total_orders': total_orders,'ofdelivery':ofdelivery,
               'delivered': delivered, 'pending': pending}

    return render(request, 'accounts/user.html', {'context':context})

@login_required(login_url='login')
def logoutUser(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
@allowed_user(allowed_roles=['admin','employee'])
def home(request):
    orders = Order.objects.all()
    orders_reversed = orders[::-1]
    customers = Customer.objects.all()
    total_customer = customers.count()
    total_orders = orders.count()
    mfilter = OrderFilter(request.GET, queryset=orders)
    orders = mfilter.qs
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    ofdelivery = orders.filter(status='Out for delivery').count()
    context = {'orders': orders, 'orders_reversed': orders_reversed, 'customers': customers,'ofdelivery':ofdelivery,
               'total_customer': total_customer, 'total_orders': total_orders,
               'delivered': delivered, 'pending': pending,'mfilter': mfilter}
    return render(request, 'accounts/dashboard.html', {'context': context})


@login_required(login_url='login')
@allowed_user(allowed_roles=['admin','employee'])
def products(request):
    products = Product.objects.all()
    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        price = request.POST.get('price')
        
        product = Product(name=name, category=category, price=price)
        product.save()
        return redirect('/')
    else:
        products = Product.objects.all()
    return render(request, 'accounts/products.html', {'products': products})


@login_required(login_url='login')
def customer(request, pk):
    customer = Customer.objects.get(id=pk)
    orders = customer.order_set.all()
    total_order = orders.count()
    orders_reversed = orders[::-1]
    mfilter = OrderFilter(request.GET, queryset=orders)
    orders = mfilter.qs
    delivered = orders.filter(status='Delivered').count()
    pending = orders.filter(status='Pending').count()
    ofdelivery = orders.filter(status='Out for delivery').count()
    context = {'customer': customer, 'orders': orders,'ofdelivery':ofdelivery,'pending':pending,'delivered':delivered,
               'total_order': total_order, 'mfilter': mfilter,'orders_reversed': orders_reversed}

    return render(request, 'accounts/customer.html', {'context': context})




@login_required(login_url='login')
def createOrder(request, pk):
    OrderFormSet = inlineformset_factory(Customer, Order, fields=('product', 'status'), extra=5)
    customer = Customer.objects.get(id=pk)
    customer_name = customer.name
    # form = OrderForm(initial={'customer':customer})
    formset = OrderFormSet(queryset=Order.objects.none(), instance=customer)

    if request.method == 'POST':
        # print('Printing POST:', request.POST)
        # form = OrderForm(request.POST)
        formset = OrderFormSet(request.POST, instance=customer)
        if formset.is_valid():
            formset.save()
            return redirect('/')

    context = {'formset': formset, 'customer': customer, 'customer_name': customer_name}
    return render(request, 'accounts/order_form.html', context)


@login_required(login_url='login')
def updateOrder(request, pk):
    order = Order.objects.get(id=pk)
    form = OrderForm(instance=order)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            # Update the status field in the database
            #order.status = form.cleaned_data['status']
            order=form.save()
            return redirect('/')

    context = {'form': form, "item": order, "order_c": order.customer}
    return render(request, 'accounts/update_form.html', context)


@login_required(login_url='login')
def deleteOrder(request, ppk):
    order = Order.objects.get(id=ppk)

    if request.method == 'POST':
        order.delete()
        return redirect('/')

    context = {"item": order, "order_c": order.customer}
    return render(request, 'accounts/delete.html', context)


@login_required(login_url='login')
def updateCustomer(request, pk):
    customer = Customer.objects.get(id=pk)
    form = CustomerForm(instance=customer)

    if request.method == 'POST':
        form = CustomerForm(request.POST, request.FILES, instance=customer)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form': form,'customer':customer}
    return render(request, 'accounts/account_settings.html', {'context':context})


@login_required(login_url='login')
def accountSettings(request):
    customer = request.user.customer
    form= CustomerForm(instance=customer)

    if request.method == "POST":
        form = CustomerForm(request.POST, request.FILES,instance=customer)
        if form.is_valid():
            form.save()
    context = {'form':form}
    return render(request, 'accounts/account_settings.html',{'context':context})



@login_required(login_url='login')
@allowed_user(allowed_roles=['admin'])
def deleteCustomer(request, ppk):
    customer = Customer.objects.get(id=ppk)

    if request.method == 'POST':
        customer.delete()
        return redirect('/')

    context = {"customer": customer}
    return render(request, 'accounts/delete_customer.html', {'context':context})

@login_required(login_url='login')
def createCustomer(request):
    form = CustomerForm()

    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/')

    context = {'form': form}
    return render(request, 'accounts/create_customer.html', context)


@login_required(login_url='login')
def place_order(request):
    if request.method == 'POST':
        form = OrderFormss(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            customer = request.user.customer
            status = 'Pending'
            order = Order(product=product, customer=customer, status=status)
            order.save()
            return redirect('/')
    else:
        form = OrderFormss(initial={'status': 'Pending'})  # Set the initial status to 'Pending'

    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('category')
        price = request.POST.get('price')
        product = Product(name=name, category=category, price=price)
        product.save()
        return redirect('/')
    else:
        products = Product.objects.all()

    return render(request, 'accounts/place_order.html', {'form': form, 'products': products})
