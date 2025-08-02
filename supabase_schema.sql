-- Fall In App Database Schema for Supabase PostgreSQL
-- Run this in your Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    age INTEGER,
    pronouns TEXT,
    department TEXT,
    year TEXT,
    looking_for TEXT,
    bio TEXT,
    profile_photo TEXT,
    is_verified BOOLEAN DEFAULT FALSE,
    otp_code TEXT,
    otp_expires TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User prompts table
CREATE TABLE IF NOT EXISTS user_prompts (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    prompt_question TEXT,
    prompt_answer TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user1_id UUID REFERENCES users(id) ON DELETE CASCADE,
    user2_id UUID REFERENCES users(id) ON DELETE CASCADE,
    matched_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user1_id, user2_id)
);

-- Likes table
CREATE TABLE IF NOT EXISTS likes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    liker_id UUID REFERENCES users(id) ON DELETE CASCADE,
    liked_id UUID REFERENCES users(id) ON DELETE CASCADE,
    liked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(liker_id, liked_id)
);

-- Chat requests table
CREATE TABLE IF NOT EXISTS chat_requests (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    requester_id UUID REFERENCES users(id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(requester_id, receiver_id)
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    sender_id UUID REFERENCES users(id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_read BOOLEAN DEFAULT FALSE
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    from_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type TEXT NOT NULL, -- 'like', 'match', 'chat_request', etc.
    message TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_verified ON users(is_verified);
CREATE INDEX IF NOT EXISTS idx_user_prompts_user_id ON user_prompts(user_id);
CREATE INDEX IF NOT EXISTS idx_matches_user1 ON matches(user1_id);
CREATE INDEX IF NOT EXISTS idx_matches_user2 ON matches(user2_id);
CREATE INDEX IF NOT EXISTS idx_likes_liker ON likes(liker_id);
CREATE INDEX IF NOT EXISTS idx_likes_liked ON likes(liked_id);
CREATE INDEX IF NOT EXISTS idx_chat_requests_requester ON chat_requests(requester_id);
CREATE INDEX IF NOT EXISTS idx_chat_requests_receiver ON chat_requests(receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_receiver ON messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- For development: Disable Row Level Security to allow Flask sessions to work
-- Comment out the RLS policies below if you want to enable them for production

-- Enable Row Level Security (RLS) - DISABLED FOR DEVELOPMENT
-- ALTER TABLE users ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_prompts ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE likes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE chat_requests ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Create policies (basic - you can customize these) - DISABLED FOR DEVELOPMENT
-- CREATE POLICY "Users can view all users" ON users FOR SELECT USING (true);
-- CREATE POLICY "Users can update their own profile" ON users FOR UPDATE USING (auth.uid()::text = id::text);
-- CREATE POLICY "Users can insert their own profile" ON users FOR INSERT WITH CHECK (true);

-- CREATE POLICY "User prompts are viewable by all" ON user_prompts FOR SELECT USING (true);
-- CREATE POLICY "Users can manage their own prompts" ON user_prompts FOR ALL USING (auth.uid()::text = user_id::text);

-- CREATE POLICY "Matches are viewable by participants" ON matches FOR SELECT USING (auth.uid()::text = user1_id::text OR auth.uid()::text = user2_id::text);
-- CREATE POLICY "Users can create matches" ON matches FOR INSERT WITH CHECK (true);

-- CREATE POLICY "Likes are viewable by all" ON likes FOR SELECT USING (true);
-- CREATE POLICY "Users can create likes" ON likes FOR INSERT WITH CHECK (true);

-- CREATE POLICY "Chat requests are viewable by participants" ON chat_requests FOR SELECT USING (auth.uid()::text = requester_id::text OR auth.uid()::text = receiver_id::text);
-- CREATE POLICY "Users can create chat requests" ON chat_requests FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Users can update chat requests" ON chat_requests FOR UPDATE USING (auth.uid()::text = receiver_id::text);

-- CREATE POLICY "Messages are viewable by participants" ON messages FOR SELECT USING (auth.uid()::text = sender_id::text OR auth.uid()::text = receiver_id::text);
-- CREATE POLICY "Users can send messages" ON messages FOR INSERT WITH CHECK (auth.uid()::text = sender_id::text);

-- CREATE POLICY "Notifications are viewable by recipient" ON notifications FOR SELECT USING (auth.uid()::text = user_id::text);
-- CREATE POLICY "Users can create notifications" ON notifications FOR INSERT WITH CHECK (true);
-- CREATE POLICY "Users can update their own notifications" ON notifications FOR UPDATE USING (auth.uid()::text = user_id::text); 