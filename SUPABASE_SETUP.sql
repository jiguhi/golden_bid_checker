create table if not exists public.naver_sessions (
  session_key text primary key,
  auth_state jsonb not null,
  updated_at timestamptz not null default now()
);

-- 이 테이블은 Streamlit 서버의 service_role key로만 접근하도록 사용하세요.
alter table public.naver_sessions enable row level security;
