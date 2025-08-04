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

-- Confession comments table for nested comments (like Reddit)
CREATE TABLE IF NOT EXISTS confession_comments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    confession_id UUID REFERENCES confessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE, -- Anonymous but tracked
    parent_comment_id UUID REFERENCES confession_comments(id) ON DELETE CASCADE, -- For nested replies
    content TEXT NOT NULL,
    likes_count INTEGER DEFAULT 0,
    is_approved BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Comment likes table
CREATE TABLE IF NOT EXISTS comment_likes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    comment_id UUID REFERENCES confession_comments(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(comment_id, user_id)
);

-- Create indexes for confessions tables
CREATE INDEX IF NOT EXISTS idx_confessions_user_id ON confessions(user_id);
CREATE INDEX IF NOT EXISTS idx_confessions_category ON confessions(category);
CREATE INDEX IF NOT EXISTS idx_confessions_created_at ON confessions(created_at);
CREATE INDEX IF NOT EXISTS idx_confession_likes_confession_id ON confession_likes(confession_id);
CREATE INDEX IF NOT EXISTS idx_confession_likes_user_id ON confession_likes(user_id);

-- Create indexes for comments tables
CREATE INDEX IF NOT EXISTS idx_confession_comments_confession_id ON confession_comments(confession_id);
CREATE INDEX IF NOT EXISTS idx_confession_comments_user_id ON confession_comments(user_id);
CREATE INDEX IF NOT EXISTS idx_confession_comments_parent_id ON confession_comments(parent_comment_id);
CREATE INDEX IF NOT EXISTS idx_confession_comments_created_at ON confession_comments(created_at);
CREATE INDEX IF NOT EXISTS idx_comment_likes_comment_id ON comment_likes(comment_id);
CREATE INDEX IF NOT EXISTS idx_comment_likes_user_id ON comment_likes(user_id); 