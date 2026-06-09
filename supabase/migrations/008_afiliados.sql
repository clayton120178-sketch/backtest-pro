-- =====================================================
-- Programa de Afiliados — Migration 008
-- Aprovado: Clayton + Ivan, jun/2026
-- =====================================================

-- Config global (singleton)
create table public.affiliate_settings (
  id               boolean primary key default true check (id),
  require_approval boolean not null default false,
  hold_days        int not null default 7,
  min_payout       numeric(12,2) not null default 50.00,
  updated_at       timestamptz not null default now()
);
insert into public.affiliate_settings (id) values (true);

-- Escada de tiers
create table public.affiliate_tiers (
  id                 uuid primary key default gen_random_uuid(),
  name               text not null,
  min_active_clients int not null,
  commission_percent numeric(5,2) not null,
  active             boolean not null default true,
  created_at         timestamptz not null default now()
);
insert into public.affiliate_tiers (name, min_active_clients, commission_percent) values
  ('Afiliado',    1, 20.00),
  ('Parceiro',   20, 25.00),
  ('Embaixador', 50, 30.00);

-- Parceiros
create table public.affiliates (
  id                          uuid primary key default gen_random_uuid(),
  user_id                     uuid not null unique references public.users(id) on delete cascade,
  display_name                text not null,
  status                      text not null default 'active'
                              check (status in ('active','paused','banned','pending')),
  pix_key                     text,
  pix_key_type                text check (pix_key_type in ('cpf','cnpj','email','phone','random')),
  commission_override_percent numeric(5,2),
  signup_source               text not null default 'self'
                              check (signup_source in ('self','admin')),
  terms_accepted_at           timestamptz,
  notes                       text,
  created_at                  timestamptz not null default now(),
  updated_at                  timestamptz not null default now()
);

-- Cupons
create table public.coupons (
  id                uuid primary key default gen_random_uuid(),
  code              text not null unique,
  affiliate_id      uuid references public.affiliates(id) on delete cascade,
  discount_type     text not null default 'percent'
                    check (discount_type in ('percent','fixed','none')),
  discount_value    numeric(12,2) not null default 10,
  applies_to        text not null default 'all_purchases'
                    check (applies_to in ('first_purchase','all_purchases')),
  valid_from        timestamptz,
  valid_until       timestamptz,
  max_redemptions   int,
  redemptions_count int not null default 0,
  status            text not null default 'active'
                    check (status in ('active','inactive')),
  created_at        timestamptz not null default now()
);
create index idx_coupons_active_code on public.coupons (upper(code)) where status = 'active';

-- Vínculo permanente cliente↔parceiro (first-touch)
create table public.affiliate_referrals (
  id               uuid primary key default gen_random_uuid(),
  affiliate_id     uuid not null references public.affiliates(id) on delete cascade,
  referred_user_id uuid not null unique references public.users(id) on delete cascade,
  coupon_id        uuid references public.coupons(id) on delete set null,
  status           text not null default 'active'
                   check (status in ('active','inactive')),
  bonded_at        timestamptz not null default now()
);

-- Comissões
create table public.affiliate_commissions (
  id                uuid primary key default gen_random_uuid(),
  affiliate_id      uuid not null references public.affiliates(id) on delete cascade,
  referral_id       uuid not null references public.affiliate_referrals(id) on delete cascade,
  referred_user_id  uuid not null references public.users(id) on delete cascade,
  subscription_id   uuid references public.subscriptions(id) on delete set null,
  plan              text not null,
  cycle             text not null,
  gross_amount      numeric(12,2) not null,
  discount_amount   numeric(12,2) not null default 0,
  net_amount        numeric(12,2) not null,
  tier_name         text not null,
  active_clients    int not null,
  commission_rate   numeric(5,2) not null,
  commission_amount numeric(12,2) not null,
  status            text not null default 'pending'
                    check (status in ('pending','approved','reversed','paid')),
  mp_payment_ref    text not null unique,
  payout_id         uuid,
  created_at        timestamptz not null default now(),
  cleared_at        timestamptz,
  paid_at           timestamptz
);
create index idx_aff_com_affiliate_status on public.affiliate_commissions (affiliate_id, status);

-- Payouts
create table public.affiliate_payouts (
  id            uuid primary key default gen_random_uuid(),
  affiliate_id  uuid not null references public.affiliates(id) on delete cascade,
  amount        numeric(12,2) not null,
  method        text not null default 'pix',
  pix_key       text,
  status        text not null default 'processing'
                check (status in ('processing','paid','failed')),
  reference_month text,
  reference     text,
  paid_by       uuid references public.users(id) on delete set null,
  created_at    timestamptz not null default now(),
  paid_at       timestamptz
);
alter table public.affiliate_commissions
  add constraint fk_commission_payout
  foreign key (payout_id) references public.affiliate_payouts(id) on delete set null;

-- =====================================================
-- Funções SQL
-- =====================================================

create or replace function public.affiliate_active_clients(p_affiliate uuid)
returns int language sql stable as $$
  select count(distinct ar.referred_user_id)::int
  from public.affiliate_referrals ar
  join public.subscriptions s on s.user_id = ar.referred_user_id and s.status = 'active'
  where ar.affiliate_id = p_affiliate
    and ar.status = 'active';
$$;

create or replace function public.resolve_affiliate_tier(p_affiliate uuid)
returns table(tier_name text, active_clients int, commission_percent numeric)
language plpgsql stable as $$
declare
  v_override numeric;
  v_count    int;
begin
  select commission_override_percent into v_override
    from public.affiliates where id = p_affiliate;

  v_count := public.affiliate_active_clients(p_affiliate);

  if v_override is not null then
    return query select 'Override'::text, v_count, v_override;
    return;
  end if;

  return query
    select t.name, v_count, t.commission_percent
    from public.affiliate_tiers t
    where t.active and t.min_active_clients <= v_count
    order by t.min_active_clients desc
    limit 1;

  if not found then
    return query select 'Afiliado'::text, v_count, 20.00::numeric;
  end if;
end; $$;

create or replace function public.validate_coupon(p_code text)
returns table(valid boolean, discount_type text, discount_value numeric, applies_to text)
language plpgsql security definer set search_path = public as $$
declare c record;
begin
  select * into c from public.coupons
    where code = upper(trim(p_code))
      and status = 'active'
      and (valid_from is null or valid_from <= now())
      and (valid_until is null or valid_until >= now())
      and (max_redemptions is null or redemptions_count < max_redemptions)
    limit 1;
  if not found then
    return query select false, null::text, null::numeric, null::text;
    return;
  end if;
  return query select true, c.discount_type, c.discount_value, c.applies_to;
end; $$;
grant execute on function public.validate_coupon(text) to anon, authenticated;

-- =====================================================
-- RLS
-- =====================================================

alter table public.affiliates            enable row level security;
alter table public.coupons               enable row level security;
alter table public.affiliate_referrals   enable row level security;
alter table public.affiliate_commissions enable row level security;
alter table public.affiliate_payouts     enable row level security;
alter table public.affiliate_tiers       enable row level security;
alter table public.affiliate_settings    enable row level security;

create or replace function public.is_admin() returns boolean language sql stable as $$
  select coalesce((auth.jwt() ->> 'email') in (
    'clayton120178@gmail.com', 'ivans.lins@gmail.com'
  ), false);
$$;

create policy aff_select on public.affiliates for select to authenticated
  using (user_id = auth.uid() or public.is_admin());
create policy aff_admin_all on public.affiliates for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

create policy cpn_admin on public.coupons for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

create policy ref_select on public.affiliate_referrals for select to authenticated
  using (public.is_admin() or affiliate_id in (
    select id from public.affiliates where user_id = auth.uid()
  ));

create policy com_select on public.affiliate_commissions for select to authenticated
  using (public.is_admin() or affiliate_id in (
    select id from public.affiliates where user_id = auth.uid()
  ));

create policy pay_select on public.affiliate_payouts for select to authenticated
  using (public.is_admin() or affiliate_id in (
    select id from public.affiliates where user_id = auth.uid()
  ));
create policy pay_admin on public.affiliate_payouts for all to authenticated
  using (public.is_admin()) with check (public.is_admin());

create policy tier_read  on public.affiliate_tiers    for select to authenticated using (true);
create policy tier_admin on public.affiliate_tiers    for all    to authenticated
  using (public.is_admin()) with check (public.is_admin());
create policy set_read   on public.affiliate_settings for select to authenticated using (true);
create policy set_admin  on public.affiliate_settings for all    to authenticated
  using (public.is_admin()) with check (public.is_admin());

-- =====================================================
-- Grants
-- =====================================================

grant usage on schema public to service_role, authenticated, anon;
grant all   on all tables in schema public to service_role;
grant select on public.affiliate_tiers, public.affiliate_settings to authenticated;

-- =====================================================
-- pg_cron
-- =====================================================

select cron.schedule('clear-affiliate-commissions', '0 4 * * *', $$
  update public.affiliate_commissions
  set status = 'approved', cleared_at = now()
  where status = 'pending'
    and created_at < now() - (
      select make_interval(days => hold_days) from public.affiliate_settings where id = true
    )
$$);

select cron.schedule('generate-monthly-payouts', '0 6 7 * *', $$
  with eligible as (
    select c.affiliate_id,
           sum(c.commission_amount) as total,
           array_agg(c.id) as commission_ids
    from public.affiliate_commissions c
    join public.affiliates a on a.id = c.affiliate_id and a.status = 'active'
    where c.status = 'approved'
      and c.created_at < date_trunc('month', now())
    group by c.affiliate_id
    having sum(c.commission_amount) >= (
      select min_payout from public.affiliate_settings where id = true
    )
  ),
  new_payouts as (
    insert into public.affiliate_payouts (affiliate_id, amount, pix_key, reference_month, status)
    select e.affiliate_id,
           e.total,
           a.pix_key,
           to_char(date_trunc('month', now()) - interval '1 day', 'YYYY-MM'),
           'processing'
    from eligible e
    join public.affiliates a on a.id = e.affiliate_id
    returning id, affiliate_id
  )
  update public.affiliate_commissions c
  set payout_id = np.id, status = 'paid', paid_at = now()
  from new_payouts np
  where c.affiliate_id = np.affiliate_id
    and c.status = 'approved'
    and c.created_at < date_trunc('month', now())
$$);
