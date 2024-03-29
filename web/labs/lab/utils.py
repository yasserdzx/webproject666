import requests
import logging
from django.conf import settings
from .models import Product

logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, message):
    token = settings.TELEGRAM_BOT_TOKEN
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=data)
    logger.debug(response.text)  # Log the API response text
    return response.json()

def process_telegram_event(event):
    message = event.get('message', {})
    text = message.get('text', '').strip()
    chat_id = message.get('chat', {}).get('id')
    user_id = str(message.get('from', {}).get('id'))

    is_admin = user_id in settings.TELEGRAM_BOT_ADMINS

    if text.startswith('/latest'):
        response_message = get_latest_phones()
        send_telegram_message(chat_id, response_message)

    elif text.startswith('/search'):
        query = text.split(' ', 1)[1] if len(text.split(' ', 1)) > 1 else ''
        response_message = search_products(query)
        send_telegram_message(chat_id, response_message)

    elif text.startswith('/categories'):
        if is_admin:
            response_message = get_category_list()
            send_telegram_message(chat_id, response_message)
        else:
            send_telegram_message(chat_id, "Sorry, you're not authorized to use this command.")


    if text.startswith('/deleteproduct'):
        # Extracting the product name from the command text
        if is_admin:
            parts = text.split(maxsplit=1)
            if len(parts) < 2:
                send_telegram_message(chat_id, "Please specify the product name to delete.")
                return

            product_name = parts[1]
            response_message = delete_product_by_name(chat_id, product_name)

        else:
            send_telegram_message(chat_id, "Sorry, you're not authorized to use this command.")

        send_telegram_message(chat_id, response_message)
def get_latest_phones():
    # Fetch the latest 5 products from your database
    latest_products = Product.objects.all().order_by('-created_at')[:5]
    if not latest_products.exists():
        return "No latest products found."

    message_lines = ["Latest Products:"]
    for product in latest_products:
        # Assuming you want to include the name and price in the message
        # Adjust the fields as per your Product model
        message_lines.append(f"{product.name} - Price: {product.price}")

    return "\n".join(message_lines)

def search_products(query):
    # Assuming 'name' is a field on your Product model
    matching_products = Product.objects.filter(name__icontains=query)
    if not matching_products.exists():
        return "No products found matching your query."

    message_lines = ["Search Results:"]
    for product in matching_products:
        # Customize this message format as needed
        message_lines.append(f"{product.name} - Price: {product.price}")

    return "\n".join(message_lines)

def get_category_list():
    from .models import Category  # Import the Category model
    categories = Category.objects.all()
    if not categories.exists():
        return "No categories found."

    message_lines = ["Available Categories:"]
    for category in categories:
        # Assuming the Category model has a 'name' field
        message_lines.append(f"- {category.name}")

    return "\n".join(message_lines)
def delete_product_by_name(chat_id, product_name):
    from .models import Product
    # Ensure that only admins can delete products
    if str(chat_id) not in settings.TELEGRAM_BOT_ADMINS:
        return "You do not have permission to delete products."

    # Fetch products with the given name (case insensitive)
    matching_products = Product.objects.filter(name__iexact=product_name)
    
    if not matching_products.exists():
        return "Product not found."

    matching_products.first().delete()
