-- Meridian HR Agent — Initial Schema
-- Run this once in the Supabase SQL Editor before starting the app.

-- Enable pgvector extension
create extension if not exists vector;

-- 1. Employees (HRIS records)
create table if not exists employees (
    id          uuid primary key default gen_random_uuid(),
    first_name  text not null,
    last_name   text not null,
    email       text not null unique,
    department  text,
    title       text,
    hire_date   timestamptz,
    manager_id  text,
    manager_email text,
    employment_type text,
    location    text,
    benefits_tier text,
    created_at  timestamptz default now()
);

-- 2. Onboarding Progress (step-by-step state machine per employee)
create table if not exists onboarding_progress (
    id          uuid primary key default gen_random_uuid(),
    employee_id uuid not null references employees(id) on delete cascade,
    status      text not null default 'in_progress',
    steps       jsonb not null default '{}',
    escalations jsonb not null default '[]',
    last_updated timestamptz default now()
);

-- 3. Escalations (human review queue)
create table if not exists escalations (
    id          uuid primary key default gen_random_uuid(),
    employee_id uuid not null references employees(id) on delete cascade,
    type        text not null,
    severity    text not null default 'medium',
    reason      text not null,
    context     jsonb default '{}',
    assigned_to text,
    status      text not null default 'pending',
    created_at  timestamptz default now(),
    resolved_at timestamptz,
    resolution  text
);

-- 4. Policy Documents (RAG chunks with embeddings)
create table if not exists policy_documents (
    id          uuid primary key default gen_random_uuid(),
    title       text not null,
    content     text not null,
    category    text,
    source_file text,
    embedding   vector(1536),
    version     text,
    created_at  timestamptz default now()
);

-- Index for fast vector similarity search
create index if not exists policy_documents_embedding_idx
    on policy_documents using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- 5. Agent Actions (audit log)
create table if not exists agent_actions (
    id          uuid primary key default gen_random_uuid(),
    agent_name  text not null,
    action_type text not null,
    employee_id uuid references employees(id) on delete set null,
    input       jsonb,
    output      jsonb,
    timestamp   timestamptz default now(),
    status      text not null default 'success',
    error       text
);
