from aiogram import types, Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from app.dao.dao import GiftDAO, PaymentDAO, UserDAO
from app.dao.session_maker import async_session_maker
from app.config import settings
from app.giftme.schemas import PaymentCreate, UserFilterPydantic  
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
    logging.info(f"Received successful payment: {message}")
    try:
        if not message.successful_payment:
            logging.error("No successful_payment data in message")
            return
        payment_info = message.successful_payment
        gift_id = int(payment_info.invoice_payload)
        stars_amount = payment_info.total_amount 
        
        async with async_session_maker() as session:
            # Retrieve the user from the database using telegram_id
            user = await UserDAO.find_one_or_none(session=session, filters=UserFilterPydantic(telegram_id=message.from_user.id))
            if not user:
                logging.error(f"Error when saving payment: User {message.from_user.id} not found in the database")
                raise Exception("User not found in the database")
            
            # Save payment record with the client's DB id
            logging.info(f"Payment received for user {user.id} for gift {gift_id} with amount {stars_amount}")
            logging.info(f"message.successful_payment data: {payment_info}")

            if payment_info:
                payment_charge_id = payment_info.telegram_payment_charge_id
            else:
                payment_charge_id = ""

            payment_data = PaymentCreate(
                user_id=user.id,  # Use the client's DB id
                gift_id=gift_id,
                amount=stars_amount,
                telegram_payment_charge_id=payment_charge_id
            )
            await PaymentDAO.add_payment(session, payment_data)
            
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
