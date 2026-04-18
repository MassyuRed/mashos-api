-- EmlisAI derived user model store
-- Purpose:
--   Persist the compact/deep derived user model used by the immediate reply
--   observation kernel. This table stores compressed, user-scoped memory only;
--   canonical history remains the source of truth in emotions / today-question
--   related tables.

create table if not exists public.emlis_ai_user_models (
    user_id text primary key,
    schema_version text not null,
    model_tier text not null,
    source_cursor jsonb not null default '{}'::jsonb,
    model_json jsonb not null default '{}'::jsonb,
    updated_at timestamptz not null default timezone('utc', now()),
    constraint emlis_ai_user_models_source_cursor_is_object
        check (jsonb_typeof(source_cursor) = 'object'),
    constraint emlis_ai_user_models_model_json_is_object
        check (jsonb_typeof(model_json) = 'object')
);

create index if not exists idx_emlis_ai_user_models_updated_at
    on public.emlis_ai_user_models (updated_at desc);

create index if not exists idx_emlis_ai_user_models_model_tier
    on public.emlis_ai_user_models (model_tier);

alter table public.emlis_ai_user_models enable row level security;

do $$
begin
    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'emlis_ai_user_models'
          and policyname = 'emlis_ai_user_models_owner_read'
    ) then
        create policy emlis_ai_user_models_owner_read
            on public.emlis_ai_user_models
            for select
            using (auth.uid()::text = user_id);
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'emlis_ai_user_models'
          and policyname = 'emlis_ai_user_models_owner_upsert'
    ) then
        create policy emlis_ai_user_models_owner_upsert
            on public.emlis_ai_user_models
            for insert
            with check (auth.uid()::text = user_id);
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'emlis_ai_user_models'
          and policyname = 'emlis_ai_user_models_owner_update'
    ) then
        create policy emlis_ai_user_models_owner_update
            on public.emlis_ai_user_models
            for update
            using (auth.uid()::text = user_id)
            with check (auth.uid()::text = user_id);
    end if;
end$$;

comment on table public.emlis_ai_user_models is
    'EmlisAI derived user model. Stores compressed, user-scoped interpretive memory for immediate replies; canonical history remains the source of truth.';

comment on column public.emlis_ai_user_models.source_cursor is
    'Tracks the latest canonical records incorporated into the derived model.';

comment on column public.emlis_ai_user_models.model_json is
    'Derived user model payload (facts, interpretive frame, hypotheses, anchors, debug).';
