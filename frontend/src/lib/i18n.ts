// ============================================================
// ANDROMEDA — Internacionalización (i18n)
// Sistema ligero: sin dependencias externas.
// Idiomas: Español (es) · English (en) · 日本語 (ja)
// ============================================================

export type Locale = "es" | "en" | "ja";

export const LOCALES: { value: Locale; label: string; flag: string }[] = [
  { value: "es", label: "Español", flag: "🇪🇸" },
  { value: "en", label: "English", flag: "🇺🇸" },
  { value: "ja", label: "日本語",  flag: "🇯🇵" },
];

export const LOCALE_STORAGE_KEY = "andromeda_locale";

// ── Diccionario de traducciones ───────────────────────────────────────────────
// Cada hoja del árbol es un objeto { es, en, ja }.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const T: Record<string, any> = {
  nav: {
    menu:          { es: "Menú",           en: "Menu",            ja: "メニュー" },
    dashboard:     { es: "Dashboard",      en: "Dashboard",       ja: "ダッシュボード" },
    chat:          { es: "Chat",           en: "Chat",            ja: "チャット" },
    companies:     { es: "Empresas",       en: "Companies",       ja: "企業" },
    users:         { es: "Usuarios",       en: "Users",           ja: "ユーザー" },
    metrics:       { es: "Métricas",       en: "Metrics",         ja: "メトリクス" },
    configuration: { es: "Configuración",  en: "Configuration",   ja: "設定" },
    myCompany:     { es: "Mi empresa",     en: "My company",      ja: "自社設定" },
    myProfile:     { es: "Mi perfil",      en: "My profile",      ja: "マイプロフィール" },
    logout:        { es: "Cerrar sesión",  en: "Log out",         ja: "ログアウト" },
    language:      { es: "Idioma",         en: "Language",        ja: "言語" },
  },

  login: {
    subtitle:         { es: "Advanced Neural Data Resource for Operations, Management, and Enterprise Assistance",
                        en: "Advanced Neural Data Resource for Operations, Management, and Enterprise Assistance",
                        ja: "企業の業務・管理・意思決定を支援するAIエージェント" },
    emailLabel:       { es: "Correo electrónico",   en: "Email address",    ja: "メールアドレス" },
    emailPlaceholder: { es: "usuario@empresa.com",  en: "user@company.com", ja: "user@company.com" },
    passwordLabel:    { es: "Contraseña",            en: "Password",         ja: "パスワード" },
    submit:           { es: "Iniciar sesión",        en: "Sign in",          ja: "ログイン" },
    submitting:       { es: "Iniciando sesión…",     en: "Signing in…",      ja: "ログイン中…" },
    errorConnection:  { es: "Error de conexión. Intenta de nuevo.",
                        en: "Connection error. Please try again.",
                        ja: "接続エラー。もう一度お試しください。" },
    footer:           { es: "Acceso restringido",   en: "Restricted access", ja: "アクセス制限" },
  },

  chat: {
    title:        { es: "Chat con ANDROMEDA",           en: "Chat with ANDROMEDA",               ja: "ANDROMEDAとチャット" },
    connecting:   { es: "Cargando sesión…",             en: "Loading session…",                  ja: "セッション読込中…" },
    connected:    { es: "Conectado",                    en: "Connected",                         ja: "接続済み" },
    hello:        { es: "Hola",                         en: "Hello",                             ja: "こんにちは" },
    emptyHint:    { es: "¡Hola! Escribe una consulta sobre tu ERP, por ejemplo:",
                    en: "Hello! Ask a question about your ERP, for example:",
                    ja: "こんにちは！ERPについて質問してください。例：" },
    emptyExample: { es: "«¿Cuánto se vendió este mes?»",
                    en: "«How much was sold this month?»",
                    ja: "«今月の売上高は？»" },
    placeholder:  { es: "Escribe tu consulta…",         en: "Type your question…",               ja: "質問を入力してください…" },
    send:         { es: "Enviar",                       en: "Send",                              ja: "送信" },
    thinking:     { es: "ANDROMEDA está procesando…",   en: "ANDROMEDA is processing…",          ja: "ANDROMEDA処理中…" },
    errorSend:    { es: "Error al enviar el mensaje.",  en: "Error sending message.",            ja: "メッセージ送信エラー。" },
  },

  config: {
    title:         { es: "Mi perfil",                         en: "My profile",                     ja: "マイプロフィール" },
    subtitle:      { es: "Actualiza tu información de acceso", en: "Update your access information", ja: "アクセス情報を更新" },
    nameLabel:     { es: "Nombre completo",                    en: "Full name",                      ja: "氏名" },
    emailLabel:    { es: "Correo electrónico",                  en: "Email address",                  ja: "メールアドレス" },
    emailHint:     { es: "Usado para iniciar sesión",           en: "Used to sign in",                ja: "ログインに使用" },
    rolLabel:      { es: "Rol",                                 en: "Role",                           ja: "役割" },
    areaLabel:     { es: "Área",                                en: "Area",                           ja: "担当エリア" },
    securityTitle: { es: "Cambiar contraseña",                  en: "Change password",                ja: "パスワード変更" },
    currentPw:     { es: "Contraseña actual",                   en: "Current password",               ja: "現在のパスワード" },
    currentPwHint: { es: "Requerida para cambiar contraseña",   en: "Required to change password",    ja: "パスワード変更に必要" },
    newPw:         { es: "Nueva contraseña",                    en: "New password",                   ja: "新しいパスワード" },
    confirmPw:     { es: "Confirmar contraseña nueva",          en: "Confirm new password",           ja: "新パスワードの確認" },
    pwHint:        { es: "Deja en blanco para mantener la contraseña actual",
                     en: "Leave blank to keep current password",
                     ja: "変更しない場合は空白のまま" },
    save:          { es: "Guardar cambios",                     en: "Save changes",                   ja: "変更を保存" },
    saving:        { es: "Guardando…",                          en: "Saving…",                        ja: "保存中…" },
    success:       { es: "Perfil actualizado correctamente.",   en: "Profile updated successfully.",  ja: "プロフィールが更新されました。" },
    pwMismatch:    { es: "Las contraseñas nuevas no coinciden.", en: "New passwords do not match.",   ja: "新しいパスワードが一致しません。" },
    errorLoad:     { es: "Error al cargar perfil.",             en: "Error loading profile.",         ja: "プロフィールの読み込みエラー。" },
  },

  admin: {
    dashTitle:        { es: "Panel de administración",               en: "Administration panel",              ja: "管理パネル" },
    dashSub:          { es: "Vista global de toda la plataforma ANDROMEDA SaaS",
                        en: "Global view of the entire ANDROMEDA SaaS platform",
                        ja: "ANDROMEDAプラットフォーム全体のグローバルビュー" },
    metricsTitle:     { es: "Métricas del sistema",                  en: "System metrics",                    ja: "システムメトリクス" },
    metricsSub:       { es: "Rendimiento global de todas las empresas",
                        en: "Global performance across all companies",
                        ja: "全企業のグローバルパフォーマンス" },
    refresh:          { es: "Actualizar",                            en: "Refresh",                           ja: "更新" },
    usersTitle:       { es: "Gestión de usuarios",                   en: "User management",                   ja: "ユーザー管理" },
    usersSub:         { es: "Administra accesos, roles y áreas",     en: "Manage access, roles and areas",    ja: "アクセス・ロール・エリアを管理" },
    companiesTitle:   { es: "Gestión de empresas",                   en: "Company management",                ja: "企業管理" },
    companiesSub:     { es: "Alta, edición y configuración Odoo",    en: "Add, edit and configure Odoo",      ja: "企業の追加・編集・Odoo設定" },
    configTitle:      { es: "Configuración del sistema",             en: "System configuration",              ja: "システム設定" },
    configSub:        { es: "Parámetros globales del sistema",       en: "Global system parameters",          ja: "グローバルシステムパラメーター" },
    totalCompanies:   { es: "Empresas totales",                      en: "Total companies",                   ja: "企業総数" },
    activeCompanies:  { es: "activas",                               en: "active",                            ja: "アクティブ" },
    totalUsers:       { es: "Usuarios registrados",                  en: "Registered users",                  ja: "登録ユーザー" },
    activeUsers:      { es: "activos hoy",                           en: "active today",                      ja: "本日アクティブ" },
    queriesToday:     { es: "Consultas hoy",                         en: "Queries today",                     ja: "本日のクエリ" },
    queriesMonth:     { es: "este mes",                              en: "this month",                        ja: "今月" },
    errorRate:        { es: "Tasa de error",                         en: "Error rate",                        ja: "エラー率" },
    errorRateSub:     { es: "Últimas 24 h",                          en: "Last 24 h",                         ja: "過去24時間" },
    uptime:           { es: "Uptime sistema",                        en: "System uptime",                     ja: "システム稼働率" },
    uptimeSub:        { es: "Últimos 30 días",                       en: "Last 30 days",                      ja: "過去30日間" },
    avgResponse:      { es: "Resp. promedio",                        en: "Avg. response",                     ja: "平均応答時間" },
    avgResponseSub:   { es: "Tiempo de respuesta",                   en: "Response time",                     ja: "応答時間" },
    manageCompanies:  { es: "Gestionar empresas",                    en: "Manage companies",                  ja: "企業を管理" },
    manageCompDesc:   { es: "Alta, edición y configuración Odoo",    en: "Add, edit and configure Odoo",      ja: "Odooの追加・編集・設定" },
    manageUsers:      { es: "Gestionar usuarios",                    en: "Manage users",                      ja: "ユーザーを管理" },
    manageUsersDesc:  { es: "Roles, permisos y accesos",             en: "Roles, permissions and access",     ja: "ロール・権限・アクセス" },
    viewMetrics:      { es: "Ver métricas",                          en: "View metrics",                      ja: "メトリクスを見る" },
    viewMetricsDesc:  { es: "Consultas, errores y rendimiento",      en: "Queries, errors and performance",   ja: "クエリ・エラー・パフォーマンス" },
    systemConfig:     { es: "Configuración sistema",                 en: "System configuration",              ja: "システム設定" },
    systemConfigDesc: { es: "LLM, modelos y parámetros globales",    en: "LLM, models and global parameters", ja: "LLM・モデル・グローバルパラメーター" },
    loadError:        { es: "Error al cargar dashboard.",            en: "Error loading dashboard.",          ja: "ダッシュボードの読み込みエラー。" },
    metricsError:     { es: "Error al cargar métricas.",             en: "Error loading metrics.",            ja: "メトリクスの読み込みエラー。" },
    queriesByType:    { es: "Consultas por tipo",                    en: "Queries by type",                   ja: "種類別クエリ" },
    queriesLabel:     { es: "Consultas",                             en: "Queries",                           ja: "クエリ" },
    activeCompaniesCard: { es: "Empresas activas", en: "Active companies", ja: "アクティブ企業" },
    avgDuration:      { es: "Duración promedio",                     en: "Average duration",                  ja: "平均処理時間" },
    successRate:      { es: "Tasa de éxito",                         en: "Success rate",                      ja: "成功率" },
  },

  agente: {
    metricsTitle:  { es: "Métricas de mi empresa",         en: "My company metrics",          ja: "自社メトリクス" },
    metricsSub:    { es: "Actividad de tu instancia Odoo", en: "Activity of your Odoo instance", ja: "OdooインスタンスのActivity" },
    period30:      { es: "Últimos 30 días",                en: "Last 30 days",                ja: "過去30日間" },
    period7:       { es: "Últimos 7 días",                 en: "Last 7 days",                 ja: "過去7日間" },
    period1:       { es: "Últimas 24 h",                   en: "Last 24 h",                   ja: "過去24時間" },
    configTitle:   { es: "Configuración de mi empresa",    en: "My company configuration",    ja: "自社設定" },
    configSub:     { es: "Gestiona la conexión con tu instancia Odoo",
                     en: "Manage your Odoo instance connection",
                     ja: "OdooインスタンスのConnection設定" },
    odooUrl:       { es: "URL de Odoo",                    en: "Odoo URL",                    ja: "Odoo URL" },
    odooDb:        { es: "Base de datos",                  en: "Database",                    ja: "データベース" },
    odooUser:      { es: "Usuario Odoo",                   en: "Odoo user",                   ja: "Odooユーザー" },
    odooPassword:  { es: "Contraseña Odoo",                en: "Odoo password",               ja: "Odooパスワード" },
    save:          { es: "Guardar configuración",          en: "Save configuration",          ja: "設定を保存" },
    saving:        { es: "Guardando…",                     en: "Saving…",                     ja: "保存中…" },
    loadError:     { es: "Error al cargar datos.",         en: "Error loading data.",         ja: "データ読み込みエラー。" },
  },

  common: {
    loading:   { es: "Cargando…",       en: "Loading…",     ja: "読み込み中…" },
    error:     { es: "Error",           en: "Error",         ja: "エラー" },
    save:      { es: "Guardar",         en: "Save",          ja: "保存" },
    cancel:    { es: "Cancelar",        en: "Cancel",        ja: "キャンセル" },
    create:    { es: "Crear",           en: "Create",        ja: "作成" },
    edit:      { es: "Editar",          en: "Edit",          ja: "編集" },
    delete:    { es: "Eliminar",        en: "Delete",        ja: "削除" },
    search:    { es: "Buscar…",         en: "Search…",       ja: "検索…" },
    active:    { es: "Activo",          en: "Active",        ja: "有効" },
    inactive:  { es: "Inactivo",        en: "Inactive",      ja: "無効" },
    all:       { es: "Todos",           en: "All",           ja: "すべて" },
    noResults: { es: "Sin resultados",  en: "No results",    ja: "結果なし" },
    yes:       { es: "Sí",              en: "Yes",           ja: "はい" },
    no:        { es: "No",              en: "No",            ja: "いいえ" },
    year:      { es: "año",             en: "year",          ja: "年" },
  },
};

// ── Función de acceso ─────────────────────────────────────────────────────────
export type TranslationKey = string;

export function t(locale: Locale, key: TranslationKey): string {
  const parts = key.split(".");
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  let node: any = T;
  for (const part of parts) {
    if (node == null) return key;
    node = node[part];
  }
  if (node && typeof node === "object" && locale in node) return node[locale] as string;
  if (node && typeof node === "object" && "es" in node)   return node["es"] as string;
  return key;
}
