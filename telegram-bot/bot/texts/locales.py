# telegram-bot/bot/texts/locales.py
# Estif Bingo 24/7 - Complete Localization Texts (UPDATED)

from .emojis import get_emoji

# Helper to get emojis consistently
def _e(key: str) -> str:
    return get_emoji(key)


TEXTS = {
    'en': {
        # Welcome & Start
        'welcome': f"{_e('game')} *Welcome to Estif Bingo 24/7!* {_e('game')}\n\n{_e('click')} Choose an option from the menu below:",
        
        # Registration
        'register_prompt': f"{_e('register')} *Share your contact to register:*\n\n{_e('info')} We need your phone number to verify your account and send rewards.",
        'register_success': f"{_e('success')} *Registration Successful!*\n\n{_e('phone')} Phone: `{{}}`\n{_e('game')} Start Playing: {{}}\n\n{_e('gift')} You received a welcome bonus!",
        'already_registered': f"{_e('success')} You are already registered!\n\n{_e('game')} Use /play to start playing.",
        
        # Join Required
        'join_required': f"{_e('warning')} *Join our channels first:*\n\n{_e('support')} Channel\n{_e('users')} Group",
        
        # Deposit
        'deposit_select': f"{_e('deposit')} *Select Payment Method*\n{_e('user')} Account Holder: `{{}}`",
        'deposit_selected': f"{_e('success')} *Selected: {{}}*\n{_e('user')} Holder: `{{}}`\n{_e('phone')} Number: `{{}}`\n\n{_e('money')} Enter amount (Min: 10 ETB, Max: 100,000 ETB):",
        'deposit_amount_accepted': f"{_e('success')} Amount: {{}} ETB accepted\n\n{_e('camera')} Send screenshot of payment confirmation:",
        'deposit_sent': f"{_e('success')} Deposit request sent!\n{_e('clock')} Waiting for admin approval.",
        
        # Cashout
        'cashout_not_allowed': f"{_e('error')} *Cash Out Not Allowed*\n{_e('money')} Total Deposited: {{}} ETB\n{_e('warning')} Minimum: 100 ETB required for withdrawal",
        'insufficient_balance': f"{_e('error')} *Insufficient Balance*\n{_e('money')} Your balance: 0 ETB\n{_e('deposit')} Use /deposit to add funds",
        'cashout_select': f"{_e('withdraw')} *Select Withdrawal Method:*",
        'cashout_selected': f"{_e('success')} *Selected: {{}}*\n{_e('money')} Balance: {{}} ETB\n\n{_e('money')} Enter amount (Min: 50, Max: 10,000 ETB):",
        'cashout_amount_accepted': f"{_e('success')} Amount: {{}} ETB accepted\n\n{_e('phone')} Enter your account number:",
        'cashout_sent': f"{_e('success')} Cashout request sent!\n{_e('clock')} Waiting for admin approval.",
        
        # Contact & Support
        'contact': f"{_e('support')} *Contact Center*\n\n{_e('chat')} Join our channels for 24/7 support:\n{_e('link')} [Support Channel]({{}})\n{_e('users')} [Support Group]({{}})",
        
        # Invite
        'invite': f"{_e('invite')} *Invite Friends!*\n\n{_e('link')} Share this link:\n`{{}}`\n\n{_e('gift')} You both get rewards when they register!",
        
        # Balance
        'balance': f"{_e('balance')} *Your Balance*\n{_e('money')} Main: {{:.2f}} ETB\n{_e('deposit')} Total Deposited: {{:.2f}} ETB",
        
        # Admin Approvals
        'approved_deposit': f"{_e('success')} *DEPOSIT APPROVED!*\n{_e('money')} Amount: {{:.2f}} ETB\n{_e('balance')} New Balance: {{:.2f}} ETB",
        'approved_cashout': f"{_e('success')} *WITHDRAWAL APPROVED!*\n{_e('money')} Amount: {{:.2f}} ETB\n{_e('balance')} New Balance: {{:.2f}} ETB",
        'rejected': f"{_e('error')} *REQUEST REJECTED*\n{_e('info')} Reason: {{}}",
        
        # General
        'use_menu': f"{_e('click')} Please use the menu buttons below:",
        
        # Bingo OTP
        'bingo_otp': f"{_e('lock')} *Bingo Login Code*\n\n{_e('numbers')} Your 6-digit code: `{{}}`\n\n{_e('clock')} This code expires in {{}} minutes.\n\n{_e('info')} Enter this code on the Bingo website to login.",
        'bingo_otp_button': f"{_e('lock')} Bingo Code",
        
        # Transfer
        'transfer_start': f"{_e('transfer')} *Balance Transfer*\n\n{_e('phone')} Enter receiver's phone number:",
        'transfer_receiver_found': f"{_e('success')} Receiver found: {{username}}",
        'transfer_enter_amount': f"{_e('money')} Your balance: {{balance:.2f}} ETB\n\nEnter amount to transfer (min {{min}}, max {{max}}):",
        'transfer_confirm': f"{_e('question')} *Confirm Transfer*\n\n{_e('user')} To: {{receiver}}\n{_e('money')} Amount: {{amount:.2f}} ETB\n{_e('info')} Fee: {{fee:.2f}} ETB\n{_e('money')} Total: {{total:.2f}} ETB\n\nConfirm?",
        'transfer_success': f"{_e('success')} *Transfer Successful!*\n\n{_e('money')} Sent: {{amount:.2f}} ETB to {{receiver}}\n{_e('balance')} New balance: {{balance:.2f}} ETB",
        'transfer_failed': f"{_e('error')} Transfer failed: {{reason}}",
        'transfer_cancelled': f"{_e('warning')} Transfer cancelled.",
        
        # Stats
        'stats_title': f"{_e('stats')} *Your Game Statistics*\n\n",
        'stats_rank': f"{_e('trophy')} Rank: #{{rank}}",
    },
    
    'am': {
        # Welcome & Start (Amharic)
        'welcome': f"{_e('game')} *እንኳን ወደ ኢስቲፍ ቢንጎ 24/7 በደህና መጡ!* {_e('game')}\n\n{_e('click')} ከታች ካለው ምናሌ ምርጫ ይምረጡ:",
        
        # Registration
        'register_prompt': f"{_e('register')} *እባክዎ ለመመዝገብ አድራሻዎን ያጋሩ:*\n\n{_e('info')} መለያዎን ለማረጋገጥ እና ሽልማቶችን ለመላክ ስልክ ቁጥርዎ ያስፈልገናል።",
        'register_success': f"{_e('success')} *ምዝገባ ተሳክቷል!*\n\n{_e('phone')} ስልክ: `{{}}`\n{_e('game')} ጨዋታ ለመጀመር: {{}}\n\n{_e('gift')} የእንኳን ደህና መጣችሁ ቦነስ ተቀብለዋል!",
        'already_registered': f"{_e('success')} ቀድሞውንም ተመዝግበዋል!\n\n{_e('game')} ለመጫወት /play ይጠቀሙ።",
        
        # Deposit
        'deposit_select': f"{_e('deposit')} *የክፍያ ዘዴ ይምረጡ*\n{_e('user')} ባለአካውንት: `{{}}`",
        'deposit_selected': f"{_e('success')} *ተመርጧል: {{}}*\n{_e('user')} ባለአካውንት: `{{}}`\n{_e('phone')} ቁጥር: `{{}}`\n\n{_e('money')} መጠን ያስገቡ (ዝቅተኛ: 10 ብር, ከፍተኛ: 100,000 ብር):",
        'deposit_amount_accepted': f"{_e('success')} መጠን: {{}} ብር ተቀባይነት አግኝቷል\n\n{_e('camera')} የክፍያ ማረጋገጫ ማያ ገጽ እይታ ይላኩ:",
        'deposit_sent': f"{_e('success')} የተቀማጭ ገንዘብ ጥያቄ ተልኳል!\n{_e('clock')} የአስተዳዳሪ ማጽደቅ በመጠባበቅ ላይ...",
        
        # Cashout
        'cashout_not_allowed': f"{_e('error')} *ገንዘብ ማውጣት አይቻልም*\n{_e('money')} አጠቃላይ ተቀማጭ: {{}} ብር\n{_e('warning')} ዝቅተኛ: 100 ብር ያስፈልጋል",
        'insufficient_balance': f"{_e('error')} *በቂ ገንዘብ የለም*\n{_e('money')} ቀሪ ሂሳብ: 0 ብር\n{_e('deposit')} ገንዘብ ለመጨመር /deposit ይጠቀሙ",
        'cashout_select': f"{_e('withdraw')} *የመውጫ ዘዴ ይምረጡ:*",
        'cashout_selected': f"{_e('success')} *ተመርጧል: {{}}*\n{_e('money')} ቀሪ ሂሳብ: {{}} ብር\n\n{_e('money')} መጠን ያስገቡ (ዝቅተኛ: 50, ከፍተኛ: 10,000 ብር):",
        'cashout_amount_accepted': f"{_e('success')} መጠን: {{}} ብር ተቀባይነት አግኝቷል\n\n{_e('phone')} የአካውንት ቁጥርዎን ያስገቡ:",
        'cashout_sent': f"{_e('success')} የመውጫ ጥያቄ ተልኳል!\n{_e('clock')} የአስተዳዳሪ ማጽደቅ በመጠባበቅ ላይ...",
        
        # Contact & Support
        'contact': f"{_e('support')} *ደንበኛ አገልግሎት*\n\n{_e('chat')} 24/7 ድጋፍ ለማግኘት ይቀላቀሉ:\n{_e('link')} [የድጋፍ ቻናል]({{}})\n{_e('users')} [የድጋፍ ቡድን]({{}})",
        
        # Invite
        'invite': f"{_e('invite')} *ጓደኞችን ይጋብዙ!*\n\n{_e('link')} ይህን ሊንክ ያጋሩ:\n`{{}}`\n\n{_e('gift')} ሲመዘገቡ ሁለታችሁም ሽልማት ታገኛላችሁ!",
        
        # Balance
        'balance': f"{_e('balance')} *ቀሪ ሂሳብዎ*\n{_e('money')} ዋና: {{:.2f}} ብር\n{_e('deposit')} አጠቃላይ ተቀማጭ: {{:.2f}} ብር",
        
        # Admin Approvals
        'approved_deposit': f"{_e('success')} *ተቀማጭ ገንዘብ ጸድቋል!*\n{_e('money')} መጠን: {{:.2f}} ብር\n{_e('balance')} አዲስ ቀሪ ሂሳብ: {{:.2f}} ብር",
        'approved_cashout': f"{_e('success')} *ገንዘብ ማውጣት ጸድቋል!*\n{_e('money')} መጠን: {{:.2f}} ብር\n{_e('balance')} አዲስ ቀሪ ሂሳብ: {{:.2f}} ብር",
        'rejected': f"{_e('error')} *ጥያቄ ውድቅ ተደርጓል*\n{_e('info')} ምክንያት: {{}}",
        
        # General
        'use_menu': f"{_e('click')} እባክዎ ከታች ያለውን ምናሌ ይጠቀሙ:",
        
        # Bingo OTP
        'bingo_otp': f"{_e('lock')} *የቢንጎ መግቢያ ኮድ*\n\n{_e('numbers')} 6-አሃዝ ኮድዎ: `{{}}`\n\n{_e('clock')} ይህ ኮድ በ{{}} ደቂቃ ውስጥ ያበቃል.\n\n{_e('info')} እባክዎ ይህን ኮድ በቢንጎ ድህረ ገጽ ላይ ያስገቡ።",
        'bingo_otp_button': f"{_e('lock')} የቢንጎ ኮድ",
        
        # Transfer
        'transfer_start': f"{_e('transfer')} *ገንዘብ ማስተላለፍ*\n\n{_e('phone')} የተቀባዩን ስልክ ቁጥር ያስገቡ:",
        'transfer_success': f"{_e('success')} *ገንዘብ ማስተላለፍ ተሳክቷል!*\n\n{_e('money')} {{:.2f}} ብር ላኩ\n{_e('balance')} አዲስ ቀሪ ሂሳብ: {{:.2f}} ብር",
        
        # Stats
        'stats_title': f"{_e('stats')} *የጨዋታ ስታቲስቲክስዎ*\n\n",
        'stats_rank': f"{_e('trophy')} ደረጃ: #{{rank}}",
    }
}


# ==================== HELPER FUNCTIONS ====================

def get_text(key: str, lang: str = 'en', **kwargs) -> str:
    """Get localized text by key with variable substitution"""
    try:
        text = TEXTS.get(lang, TEXTS['en']).get(key, TEXTS['en'].get(key, f"Missing text: {key}"))
        if kwargs:
            text = text.format(**kwargs)
        return text
    except Exception:
        return f"Error loading text: {key}"


def get_supported_languages() -> list:
    """Get list of supported languages"""
    return ['en', 'am']


def get_language_name(lang: str) -> str:
    """Get language display name"""
    languages = {
        'en': 'English 🇬🇧',
        'am': 'አማርኛ 🇪🇹'
    }
    return languages.get(lang, 'English')


# ==================== EXPORTS ====================
__all__ = [
    'TEXTS',
    'get_text',
    'get_supported_languages',
    'get_language_name',
]