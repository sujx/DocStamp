# Login Page Design Spec

## Layout

- **Desktop**: 60/40 split screen — left brand panel, right form
- **Mobile (<768px)**: Vertical stack — brand header bar + form below

## Brand Panel (60%)

- Background: `linear-gradient(135deg, #008a3d, #00662b)` (brand green gradient)
- Content centered vertically and horizontally:
  - Logo icon (72×72px, white semi-transparent bg, `border-radius: 18px`)
  - Title: "docStamp" (26px, 700 weight, white)
  - Subtitle: "一站式文档处理工具箱" (14px, 0.75 opacity)
- On mobile: smaller, horizontal header bar with title only

## Form Panel (40%)

- Background: white (`var(--color-surface)`)
- Content centered vertically:
  - Title "登录" (24px, 700 weight, centered)
  - Subtitle "请输入您的账户信息" (13px, text-tertiary, centered)
  - Username field (UInput, left-aligned label)
  - Password field (UInput type=password, left-aligned label)
  - "记住我" checkbox (aligned left)
  - Login button (UButton color=primary, block, 46px height)
  - "← 返回首页" link (centered, small, underlined)

## Error State

- `UAlert color="error" variant="soft"` shown above the login button when credentials fail
- Auto-dismissed on next login attempt

## Behavior

- Enter key triggers login
- On success: redirect to `/`
- On failure: show error alert
- Auth state persisted via Flask session cookie
