
-- Voucher system
CREATE TABLE IF NOT EXISTS vouchers (
    code TEXT PRIMARY KEY,
    discount_type TEXT, -- PERCENT or FIXED
    discount_value INTEGER,
    min_purchase INTEGER DEFAULT 0,
    max_uses INTEGER DEFAULT 0,
    used_count INTEGER DEFAULT 0,
    expires_at TEXT,
    aktif INTEGER DEFAULT 1
);

-- User voucher usage tracking
CREATE TABLE IF NOT EXISTS voucher_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    voucher_code TEXT,
    order_invoice TEXT,
    used_at TEXT
);

-- Referral system
CREATE TABLE IF NOT EXISTS referrals (
    referrer_id INTEGER,
    referred_id INTEGER,
    reward_claimed INTEGER DEFAULT 0,
    created_at TEXT,
    PRIMARY KEY (referrer_id, referred_id)
);

-- Testimonials
CREATE TABLE IF NOT EXISTS testimonials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    rating INTEGER,
    message TEXT,
    approved INTEGER DEFAULT 0,
    created_at TEXT
);

-- FAQ
CREATE TABLE IF NOT EXISTS faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT,
    answer TEXT,
    urutan INTEGER DEFAULT 0,
    aktif INTEGER DEFAULT 1
);

