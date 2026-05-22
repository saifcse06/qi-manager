from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Category, Product
from accounts.decorators import role_required, permission_required


@login_required
@role_required(['Super Admin', 'Admin'])
def category_list(request):
    categories = Category.objects.order_by('name')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(categories, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'products/category_list.html', context)


@login_required
@role_required(['Super Admin', 'Admin'])
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        if name:
            category = Category.objects.create(
                name=name,
                description=description,
                is_active=is_active,
                created_by=request.user
            )
            messages.success(request, 'Category created successfully!')
            return redirect('products:category_list')
        else:
            messages.error(request, 'Category name is required!')
    
    return render(request, 'products/category_form.html')


@login_required
@role_required(['Super Admin', 'Admin'])
def category_edit(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_active = request.POST.get('is_active') == 'on'
        
        if name:
            category.name = name
            category.description = description
            category.is_active = is_active
            category.updated_by = request.user
            category.save()
            messages.success(request, 'Category updated successfully!')
            return redirect('products:category_list')
        else:
            messages.error(request, 'Category name is required!')
    
    context = {
        'category': category,
    }
    return render(request, 'products/category_form.html', context)


@login_required
@role_required(['Super Admin', 'Admin'])
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.is_active = False
        category.updated_by = request.user
        category.save()
        messages.success(request, 'Category deactivated successfully!')
        return redirect('products:category_list')
    
    context = {
        'category': category,
    }
    return render(request, 'products/category_confirm_delete.html', context)


@login_required
@role_required(['Super Admin', 'Admin'])
def product_list(request):
    products = Product.objects.filter(is_deleted=False).select_related('category').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )
    
    # Filter by product type
    product_type = request.GET.get('type')
    if product_type in ['product', 'service']:
        products = products.filter(product_type=product_type)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Pagination
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = Category.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'product_type': product_type,
        'category_id': int(category_id) if category_id else None,
        'categories': categories,
    }
    return render(request, 'products/product_list.html', context)


@login_required
@role_required(['Super Admin', 'Admin'])
def product_create(request):
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        sku = request.POST.get('sku') or None
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        product_type = request.POST.get('product_type')
        unit_price = request.POST.get('unit_price')
        tax_percentage = request.POST.get('tax_percentage') or 0.00
        warranty_info = request.POST.get('warranty_info')
        status = request.POST.get('status')
        
        # Validation
        errors = []
        if not name:
            errors.append('Product name is required')
        if not category_id:
            errors.append('Category is required')
        if not product_type:
            errors.append('Product type is required')
        if not unit_price:
            errors.append('Unit price is required')
        try:
            unit_price = float(unit_price)
            if unit_price < 0:
                errors.append('Unit price must be positive')
        except ValueError:
            errors.append('Invalid unit price')
        
        try:
            tax_percentage = float(tax_percentage)
            if tax_percentage < 0 or tax_percentage > 100:
                errors.append('Tax percentage must be between 0 and 100')
        except ValueError:
            errors.append('Invalid tax percentage')
        
        if not errors:
            product = Product.objects.create(
                name=name,
                sku=sku,
                description=description,
                category_id=category_id,
                product_type=product_type,
                unit_price=unit_price,
                tax_percentage=tax_percentage,
                warranty_info=warranty_info,
                status=status,
                created_by=request.user
            )
            messages.success(request, 'Product created successfully!')
            return redirect('products:product_list')
        else:
            for error in errors:
                messages.error(request, error)
    
    context = {
        'categories': categories,
    }
    return render(request, 'products/product_form.html', context)


@login_required
@role_required(['Super Admin', 'Admin'])
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        sku = request.POST.get('sku') or None
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        product_type = request.POST.get('product_type')
        unit_price = request.POST.get('unit_price')
        tax_percentage = request.POST.get('tax_percentage') or 0.00
        warranty_info = request.POST.get('warranty_info')
        status = request.POST.get('status')
        
        # Validation
        errors = []
        if not name:
            errors.append('Product name is required')
        if not category_id:
            errors.append('Category is required')
        if not product_type:
            errors.append('Product type is required')
        if not unit_price:
            errors.append('Unit price is required')
        try:
            unit_price = float(unit_price)
            if unit_price < 0:
                errors.append('Unit price must be positive')
        except ValueError:
            errors.append('Invalid unit price')
        
        try:
            tax_percentage = float(tax_percentage)
            if tax_percentage < 0 or tax_percentage > 100:
                errors.append('Tax percentage must be between 0 and 100')
        except ValueError:
            errors.append('Invalid tax percentage')
        
        if not errors:
            product.name = name
            product.sku = sku
            product.description = description
            product.category_id = category_id
            product.product_type = product_type
            product.unit_price = unit_price
            product.tax_percentage = tax_percentage
            product.warranty_info = warranty_info
            product.status = status
            product.updated_by = request.user
            product.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('products:product_list')
        else:
            for error in errors:
                messages.error(request, error)
    
    context = {
        'product': product,
        'categories': categories,
    }
    return render(request, 'products/product_form.html', context)


@login_required
@role_required(['Super Admin', 'Admin'])
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk, is_deleted=False)
    
    if request.method == 'POST':
        product.soft_delete()
        messages.success(request, 'Product deleted successfully!')
        return redirect('products:product_list')
    
    context = {
        'product': product,
    }
    return render(request, 'products/product_confirm_delete.html', context)