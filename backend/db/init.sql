-- Table des utilisateurs
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    hashed_password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des portefeuilles Circle (liée aux utilisateurs)
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    circle_wallet_id VARCHAR(255) UNIQUE NOT NULL, -- L'ID renvoyé par Circle
    address VARCHAR(255) NOT NULL,                -- L'adresse blockchain (0x...)
    blockchain VARCHAR(50) NOT NULL,              -- ex: 'POLYGON-AMOY'
    account_type VARCHAR(20) DEFAULT 'SCA',       -- SCA pour Smart Contract Account
    state VARCHAR(20) DEFAULT 'active',
    wallet_set_id VARCHAR(255) NOT NULL
);

-- Table de suivi de consommation (pour la facturation à l'usage)
CREATE TABLE token_usage (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    model_name VARCHAR(50),                       -- 'gemini-1.5-pro', 'gpt-4o'
    tokens_consumed INTEGER NOT NULL,
    cost_usd DECIMAL(10, 6),                      -- Coût calculé en micro-dollars
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);