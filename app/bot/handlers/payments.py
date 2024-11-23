from aiogram import types, Router, F
from aiogram.types import LabeledPrice, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.dao.dao import GiftDAO, PaymentDAO
from app.dao.session_maker import async_session_maker
from app.config import settings
import logging

router = Router()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """Simple pre-checkout validation for Stars payments"""
    try:
        gift_id = int(pre_checkout_query.invoice_payload)
        await pre_checkout_query.answer(ok=True)
    except Exception as e:
        logging.error(f"Pre-checkout error: {e}")
        await pre_checkout_query.answer(
            ok=False,
            error_message="Payment validation failed"
        )

@router.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    """Handle successful Stars payment"""
    try:
        payment_info = message.successful_payment
        gift_id = int(payment_info.invoice_payload)
        stars_amount = payment_info.total_amount / 100  # Convert to Stars
        
        async with async_session_maker() as session:
            # Save payment record
            payment_dao = PaymentDAO(session)
            payment = {
                "user_id": message.from_user.id,
                "gift_id": gift_id,
                "amount": stars_amount,
                "telegram_payment_charge_id": payment_info.telegram_payment_charge_id,
                "provider_payment_charge_id": payment_info.provider_payment_charge_id
            }
            await payment_dao.add_payment(payment)
            
            # Get gift details
            gift = await GiftDAO(session).get_gift_by_id(gift_id)
            
            # Create success message
            webapp_url = f"{settings.BASE_SITE}/twa/public/gifts/{gift_id}"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="View Gift", web_app=WebAppInfo(url=webapp_url))
            ]])
            
            await message.answer(
                f"✅ Thank you! {stars_amount} Stars sent for {gift.name}!",
                reply_markup=keyboard
            )

    except Exception as e:
        logging.error(f"Error processing Stars payment: {e}")
        await message.answer(
            "Payment received but there was an error updating the gift.\n"
            "Our team will check this shortly."
        )
