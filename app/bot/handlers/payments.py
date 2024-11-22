from aiogram import types, Router
from aiogram.filters import Command
from app.utils.bot_instance import telegram_bot
from app.dao.dao import GiftDAO, PaymentDAO, async_session_maker
from app.giftme.models import Payment
import logging
from sqlalchemy.exc import SQLAlchemyError

router = Router()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    """Validate payment before processing"""
    try:
        gift_id = int(pre_checkout_query.invoice_payload)
        
        async with async_session_maker() as session:
            gift_dao = GiftDAO(session)
            gift = await gift_dao.get_gift_by_id(gift_id)
            
            if not gift:
                await telegram_bot.answer_pre_checkout_query(
                    pre_checkout_query.id,
                    ok=False,
                    error_message="Gift not found or no longer available"
                )
                return

            # Validate payment amount in Stars (XTR)
            payment_amount = pre_checkout_query.total_amount / 100
            if payment_amount <= 0 or payment_amount > gift.price:
                await telegram_bot.answer_pre_checkout_query(
                    pre_checkout_query.id,
                    ok=False,
                    error_message="Invalid payment amount"
                )
                return

            # Check if gift is still available for purchase
            total_paid = sum(p.amount for p in gift.payments)
            if total_paid + payment_amount > gift.price:
                await telegram_bot.answer_pre_checkout_query(
                    pre_checkout_query.id,
                    ok=False,
                    error_message="Gift has already been fully paid"
                )
                return
                
            await telegram_bot.answer_pre_checkout_query(
                pre_checkout_query.id,
                ok=True
            )
            
    except Exception as e:
        logging.error(f"Pre-checkout error: {e}")
        await telegram_bot.answer_pre_checkout_query(
            pre_checkout_query.id,
            ok=False,
            error_message="Payment validation failed. Please try again."
        )

@router.message(lambda message: message.successful_payment)
async def process_successful_payment(message: types.Message):
    """
    Handle successful payment and deliver digital goods.
    Store payment information for potential refunds.
    """
    try:
        payment_info = message.successful_payment
        gift_id = int(payment_info.invoice_payload)
        amount_paid = payment_info.total_amount / 100  # Convert to main currency unit
        
        async with async_session_maker() as session:
            # Create payment record
            payment = Payment(
                user_id=message.from_user.id,
                gift_id=gift_id,
                amount=amount_paid,
                telegram_payment_charge_id=payment_info.telegram_payment_charge_id,
                provider_payment_charge_id=payment_info.provider_payment_charge_id
            )
            session.add(payment)
            await session.commit()
            
            # Get gift details for confirmation message
            gift = await GiftDAO(session).get_gift_by_id(gift_id)
            
            # Send confirmation to user
            await message.answer(
                f"✅ Payment received for {gift.name}!\n\n"
                f"Amount: {amount_paid} XTR\n"
                f"Transaction ID: {payment_info.telegram_payment_charge_id}\n\n"
                "Thank you for your purchase! 🎁"
            )

    except SQLAlchemyError as e:
        logging.error(f"Database error processing payment: {e}")
        await message.answer(
            "Your payment was received, but there was an error updating our records. "
            "Please contact support with your payment ID: "
            f"{payment_info.telegram_payment_charge_id}"
        )
    except Exception as e:
        logging.error(f"Error processing successful payment: {e}")
        await message.answer(
            "There was an error processing your payment. "
            "Please contact support for assistance."
        )

@router.message(Command("paysupport"))
async def payment_support(message: types.Message):
    """Handle payment support requests"""
    await message.answer(
        "For payment support, please:\n"
        "1. Provide your Transaction ID\n"
        "2. Describe your issue\n"
        "3. Contact @YourSupportUsername\n\n"
        "We'll get back to you within 24 hours."
    )
