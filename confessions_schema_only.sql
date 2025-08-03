-- Add these new tables and indexes to your existing Fall In database
-- Run this in your Supabase SQL Editor

-- Confessions table for anonymous posts
CREATE TABLE IF NOT EXISTS confessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE, -- Anonymous but tracked for moderation
    content TEXT NOT NULL,
    category TEXT NOT NULL, -- 'crush', 'missed', 'confession', 'rant', 'appreciation', 'advice'
    likes_count INTEGER DEFAULT 0,
    views_count INTEGER DEFAULT 0,
    is_approved BOOLEAN DEFAULT TRUE, -- For moderation
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Confession likes table to track who liked which confessions
CREATE TABLE IF NOT EXISTS confession_likes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    confession_id UUID REFERENCES confessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(confession_id, user_id)
);

-- Create indexes for confessions tables
CREATE INDEX IF NOT EXISTS idx_confessions_user_id ON confessions(user_id);
CREATE INDEX IF NOT EXISTS idx_confessions_category ON confessions(category);
CREATE INDEX IF NOT EXISTS idx_confessions_created_at ON confessions(created_at);
CREATE INDEX IF NOT EXISTS idx_confession_likes_confession_id ON confession_likes(confession_id);
CREATE INDEX IF NOT EXISTS idx_confession_likes_user_id ON confession_likes(user_id); 