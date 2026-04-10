import os
import logging
import re
import requests
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

# Load environment variables
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
LLM_API_KEY = os.getenv('LLM_API_KEY')
ALLOWED_USER_IDS = set(os.getenv('ALLOWED_USER_IDS', '').split(','))

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

MESSAGE_BUFFER_DELAY = 1.0
user_buffers = {}

# Fixed model for grammar mode
GRAMMAR_MODEL = 'google/gemini-3.1-pro-preview'  # ← CHANGED

# System prompts
GRAMMAR_SYSTEM_PROMPT = """
Исправь грамматические ошибки в русском языке, используя мужской род для пользователя.
Перепиши предложение с исправлениями прямо в тексте:
- Выдели ошибки ~зачеркиванием~ (тильда с обеих сторон)
- Сразу после напиши правильное слово **жирным шрифтом** (звёздочки с обеих сторон)
Если грамматика безупречна, ответь только 👍

Пример:
Ввод: Я пошла в магазине и купила хлеб.
Вывод: Я ~пошла~ **пошёл** в ~магазине~ **магазин** и ~купила~ **купил** хлеб.

Если текст не на русском языке, или есть английские слова, переведи его на русский.
"""

DEFAULT_NORMAL_SYSTEM_PROMPT = """Всегда отвечайте на русском языке, даже если пользователь говорит по-английски"""

async def process_message_with_ai(
    text: str,
    model: str,
    system_prompt: str,
    conversation_history: list = None
) -> str:
    """Send message to Eden AI API and get response."""
    try:
        messages = [{"role": "system", "content": system_prompt}]

        if conversation_history:
            messages.extend(conversation_history)

        messages.append({"role": "user", "content": text})

        response = requests.post(
            url="https://api.edenai.run/v3/llm/chat/completions",  # ← CHANGED
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",  # ← CHANGED
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.3
            },
            timeout=120
        )

        response.raise_for_status()
        result = response.json()

        logger.info("=" * 80)
        logger.info(f"DEBUG - Model: {model}")
        logger.info(f"DEBUG - Full API Response: {result}")
        logger.info("=" * 80)

        ai_message = result['choices'][0]['message']['content'].strip()
        logger.info(f"DEBUG - Extracted AI Message: {ai_message}")

        return ai_message

    except requests.exceptions.Timeout:
        logger.error("Eden AI API request timed out after 120 seconds.")  # ← CHANGED
        return "Извините, время ожидания ответа истекло (120 сек). / Sorry, the request timed out (120s)."
    
    except Exception as e:
        logger.error(f"Error calling Eden AI API: {e}")  # ← CHANGED
        response_text = "No response"
        if 'response' in locals():
            response_text = getattr(response, 'text', 'No response text')
        logger.error(f"Response content: {response_text}")
        return "Извините, произошла ошибка. / Sorry, an error occurred."


def get_user_config(context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Get user configuration or create default."""
    if 'model' not in context.user_data:
        context.user_data['model'] = 'google/gemini-3.1-pro-preview'
    if 'system_prompt' not in context.user_data:
        context.user_data['system_prompt'] = DEFAULT_NORMAL_SYSTEM_PROMPT
    if 'memory' not in context.user_data:
        context.user_data['memory'] = 0
    if 'conversation_history' not in context.user_data:
        context.user_data['conversation_history'] = []

    return {
        'model': context.user_data['model'],
        'system_prompt': context.user_data['system_prompt'],
        'memory': context.user_data['memory']
    }

def is_user_allowed(user_id: int) -> bool:
    """Check if user is in the whitelist."""
    if not ALLOWED_USER_IDS or ALLOWED_USER_IDS == {''}:
        return True
    return str(user_id) in ALLOWED_USER_IDS


def split_message(text: str, max_length: int = 4096) -> list[str]:
    """Split a long message into chunks that fit Telegram's message length limit."""
    if len(text) <= max_length:
        return [text]

    safe_length = max_length - 100
    chunks = []
    paragraphs = text.split('\n\n')
    current_chunk = ""

    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) + 2 > safe_length:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""

            if len(paragraph) > safe_length:
                sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) + 1 > safe_length:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence
                    else:
                        current_chunk += (" " if current_chunk else "") + sentence
            else:
                current_chunk = paragraph
        else:
            current_chunk += ("\n\n" if current_chunk else "") + paragraph

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def convert_MarkdownV2_to_telegram(text: str) -> str:
    # Convert **bold** → *bold* (MarkdownV2 bold)
    text = re.sub(r'\*\*(.+?)\*\*', r'*\1*', text, flags=re.DOTALL)

    # Escape reserved MarkdownV2 characters EXCEPT '*', '~', and '_'
    text = re.sub(r'([\[\]()`>#\+\-=|{}.!\\])', r'\\\1', text)

    return text

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    await update.message.reply_text(
        "👋 Привет! I'm a multi-mode AI assistant.\n\n"
        "*Commands:*\n"
        "/normal - Normal chat mode with default settings\n"
        "/grammar - Grammar correction mode (stateless)\n"
        "/setmodel <model> - Set AI model\n"
        "/setsystem <prompt> - Set custom system prompt\n"
        "/m - Start a new conversation with infinite memory and grammar check\n"
        "/prev\\_m - Start typical infinite memory mode \\(no grammar\\)"
    )


async def grammar_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to grammar correction mode."""
    context.user_data['memory'] = 0
    context.user_data['conversation_history'] = []
    context.user_data['system_prompt'] = GRAMMAR_SYSTEM_PROMPT

    await update.message.reply_text(
        "Switched to *Grammar Mode*",
        parse_mode='MarkdownV2'
    )


async def normal_mode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Switch to normal chat mode and show current settings."""
    context.user_data['memory'] = 0
    context.user_data['conversation_history'] = []
    context.user_data['system_prompt'] = DEFAULT_NORMAL_SYSTEM_PROMPT

    config = get_user_config(context)
    history_count = len(context.user_data.get('conversation_history', []))

    if config['memory'] == 0:
        memory_desc = "0 (stateless - no conversation context)"
    elif config['memory'] in (-1, -2):
        memory_desc = "∞ (infinite - remembers everything)"
    else:
        memory_desc = f"{config['memory']} (remembers last {config['memory'] * 2} messages)"

    settings_text = (
        f"💬 *Switched to Normal Mode*\n\n"
        f"*Current Settings*\n\n"
        f"*Model:* `{config['model']}`\n"
        f"*Memory:* {memory_desc}\n"
        f"*Current history:* {history_count} messages stored\n"
        f"*System Prompt:*\n`{config['system_prompt']}`\n\n"
        f"💭 Conversation history cleared."
    )

    await update.message.reply_text(settings_text)


async def setmodel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set AI model."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /setmodel <model_name>\n\n"
            "Example: `/setmodel google/gemini-3.1-pro-preview`\n\n"
            "You can find model names at: https://app.edenai.run/"  # ← CHANGED
        )
        return

    model = ' '.join(context.args)
    context.user_data['model'] = model

    await update.message.reply_text(
        f"✅ Model updated to: `{model}`",
        parse_mode='MarkdownV2'
    )


async def setsystem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set custom system prompt."""
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /setsystem <prompt>\n\n"
            "Example: `/setsystem You are a helpful coding assistant.`"
        )
        return

    system_prompt = ' '.join(context.args)
    context.user_data['system_prompt'] = system_prompt

    await update.message.reply_text(
        f"✅ System prompt updated:\n\n`{system_prompt}`",
        parse_mode='MarkdownV2'
    )


async def setmemory_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a new conversation with infinite memory and grammar checks."""
    context.user_data['memory'] = -1
    context.user_data['conversation_history'] = []
    context.user_data['system_prompt'] = DEFAULT_NORMAL_SYSTEM_PROMPT

    await update.message.reply_text(
        "*New conversation started with infinite memory and background grammar*",
        parse_mode='MarkdownV2'
    )

async def prev_m_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start a new conversation with infinite memory and NO grammar checks (-2)."""
    context.user_data['memory'] = -2
    context.user_data['conversation_history'] = []
    context.user_data['system_prompt'] = DEFAULT_NORMAL_SYSTEM_PROMPT

    await update.message.reply_text(
        "*New typical conversation started with infinite memory \\(No Grammar\\)*",
        parse_mode='MarkdownV2'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages from users with buffering for split messages."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "Unknown"

    if not is_user_allowed(user_id):
        logger.warning(f"Unauthorized access attempt from user {user_id} (@{username})")
        await update.message.reply_text("⛔ Access denied. You are not authorized to use this bot.")
        return

    user_message = update.message.text

    if user_id not in user_buffers:
        user_buffers[user_id] = {
            'messages': [],
            'task': None,
            'context': context,
            'last_update': None
        }

    buffer = user_buffers[user_id]

    if buffer['task'] and not buffer['task'].done():
        buffer['task'].cancel()

    buffer['messages'].append(user_message)
    buffer['last_update'] = update
    buffer['context'] = context

    buffer['task'] = asyncio.create_task(
        process_buffered_messages(user_id, username)
    )


async def process_buffered_messages(user_id: int, username: str) -> None:
    """Process all buffered messages after delay."""
    try:
        await asyncio.sleep(MESSAGE_BUFFER_DELAY)

        buffer = user_buffers[user_id]

        if not buffer['messages']:
            return

        combined_message = '\n'.join(buffer['messages'])
        update = buffer['last_update']
        context = buffer['context']
        config = get_user_config(context)

        buffer['messages'] = []

        logger.info(f"Processing combined message from {user_id} (@{username})")
        logger.info(f"Combined message length: {len(combined_message)} chars")

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

        model = config['model']
        system_prompt = config['system_prompt']

        is_grammar_mode = system_prompt == GRAMMAR_SYSTEM_PROMPT
        if is_grammar_mode:
            model = GRAMMAR_MODEL

        full_history = context.user_data.get('conversation_history', [])
        memory_value = config['memory']

        # Both -1 (/m) and -2 (/prev_m) use infinite memory
        if memory_value in (-1, -2):
            conversation_history = full_history
        elif memory_value > 0:
            conversation_history = full_history[-(memory_value * 2):]
        else:
            conversation_history = []

        # Handle the special /m mode (-1): simultaneous async background grammar checker
        if memory_value == -1:
            async def fetch_and_send_grammar():
                try:
                    grammar_response = await process_message_with_ai(
                        combined_message,
                        GRAMMAR_MODEL,
                        GRAMMAR_SYSTEM_PROMPT,
                        []
                    )

                    grammar_chunks = split_message(grammar_response)
                    for i, chunk in enumerate(grammar_chunks):
                        try:
                            formatted_chunk = convert_MarkdownV2_to_telegram(chunk)
                            if len(grammar_chunks) > 1:
                                formatted_chunk = f"_Part {i+1}/{len(grammar_chunks)}_\n\n" + formatted_chunk
                            await update.message.reply_text(formatted_chunk, parse_mode='MarkdownV2')
                        except Exception as e:
                            logger.warning(f"Parse failed for grammar chunk {i+1}: {e}.")
                            await update.message.reply_text(chunk)

                        if i < len(grammar_chunks) - 1:
                            await asyncio.sleep(0.5)
                except Exception as e:
                    logger.error(f"Background grammar task failed: {e}")

            # Fire off the background task, DO NOT wait for it here
            asyncio.create_task(fetch_and_send_grammar())

            ai_response = await process_message_with_ai(
                combined_message,
                model,
                system_prompt,
                conversation_history
            )
        else:
            # Normal logic for non /m modes, including -2 (/prev_m)
            ai_response = await process_message_with_ai(
                combined_message,
                model,
                system_prompt,
                conversation_history
            )

        # Store history and send the normal bot response
        if memory_value != 0:
            if combined_message.strip().startswith('/'):
                logger.warning(f"Prevented command-like message from entering history: {combined_message}")
            else:
                if 'conversation_history' not in context.user_data:
                    context.user_data['conversation_history'] = []

                context.user_data['conversation_history'].append({"role": "user", "content": combined_message})
                context.user_data['conversation_history'].append({"role": "assistant", "content": ai_response})

                logger.info(f"Conversation history size: {len(context.user_data['conversation_history'])} messages")

        message_chunks = split_message(ai_response)
        logger.info(f"Response split into {len(message_chunks)} chunk(s)")

        for i, chunk in enumerate(message_chunks):
            try:
                if is_grammar_mode:
                    formatted_chunk = convert_MarkdownV2_to_telegram(chunk)
                    logger.info("Formatted chunk")
                    logger.info(formatted_chunk)
                    if len(message_chunks) > 1:
                        formatted_chunk = f"_Part {i+1}/{len(message_chunks)}_\n\n" + formatted_chunk
                    await update.message.reply_text(formatted_chunk, parse_mode='MarkdownV2')
                else:
                    formatted_chunk = convert_MarkdownV2_to_telegram(chunk)
                    if len(message_chunks) > 1:
                        formatted_chunk = f"_[Part {i+1}/{len(message_chunks)}]_\n\n" + formatted_chunk
                    await update.message.reply_text(formatted_chunk, parse_mode='MarkdownV2')

                logger.info(f"Sent chunk {i+1}/{len(message_chunks)} ({len(chunk)} chars)")

                if i < len(message_chunks) - 1:
                    await asyncio.sleep(0.5)

            except Exception as e:
                logger.warning(f"Parse failed for chunk {i+1}: {e}. Falling back to plain text.")

                plain_chunk = chunk
                if len(message_chunks) > 1:
                    plain_chunk = f"[Part {i+1}/{len(message_chunks)}]\n\n{chunk}"

                await update.message.reply_text(plain_chunk)

                if i < len(message_chunks) - 1:
                    await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        logger.info(f"Buffer processing cancelled for user {user_id} (new message arrived)")
    except Exception as e:
        logger.error(f"Error processing buffered messages for user {user_id}: {e}")
        if user_id in user_buffers and user_buffers[user_id]['last_update']:
            try:
                await user_buffers[user_id]['last_update'].message.reply_text(
                    "❌ An error occurred while processing your message."
                )
            except:
                pass


async def post_init(application: Application) -> None:
    """Set up bot commands menu after initialization."""
    commands = [
        BotCommand("m", "Start memory mode with grammar bot"),
        BotCommand("grammar", "Switch to grammar correction mode"),
        BotCommand("normal", "Switch to normal chat mode"),
        BotCommand("setmodel", "Set AI model"),
        BotCommand("setsystem", "Set custom system prompt"),
        BotCommand("prev_m", "Previous infinite memory mode (no grammar)"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot menu commands set successfully")


def main() -> None:
    """Start the bot."""
    if not TELEGRAM_BOT_TOKEN or not LLM_API_KEY:
        logger.error("Missing required environment variables!")
        return

    application = Application.builder().token(TELEGRAM_BOT_TOKEN).post_init(post_init).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("grammar", grammar_mode_command))
    application.add_handler(CommandHandler("normal", normal_mode_command))
    application.add_handler(CommandHandler("setmodel", setmodel_command))
    application.add_handler(CommandHandler("setsystem", setsystem_command))
    application.add_handler(CommandHandler("m", setmemory_command))
    application.add_handler(CommandHandler("prev_m", prev_m_command))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE,
        handle_message
    ))

    logger.info("Bot started in DM mode with whitelist protection...")
    logger.info("Default: memory=0, can be changed with /m or /prev_m")
    if ALLOWED_USER_IDS and ALLOWED_USER_IDS != {''}:
        logger.info(f"Allowed users: {ALLOWED_USER_IDS}")
    else:
        logger.warning("⚠️ No whitelist configured - all users allowed!")

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()