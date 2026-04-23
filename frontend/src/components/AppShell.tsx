import { Link, useLocation, useNavigate } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  Inbox,
  ShieldCheck,
  Settings,
  Search,
  Bell,
  Sparkles,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Compass,
  Zap,
  MoreHorizontal,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { clearAuthUser, getAuthUser } from "@/lib/auth";
import { useEffect, useRef, useState, type ReactNode } from "react";

const navItems = [
  { to: "/dashboard", label: "Active Disputes", icon: Inbox, badge: 6 },
  { to: "/integrity-hub", label: "Integrity Hub", icon: ShieldCheck },
  { to: "/settings", label: "Settings", icon: Settings },
] as const;

const secondaryItems = [
  { label: "Explore", icon: Compass },
  { label: "Insights", icon: Zap },
  { label: "More", icon: MoreHorizontal },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const path = location.pathname;
  const [collapsed, setCollapsed] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const authUser = getAuthUser();
  const displayName = "admin";

  useEffect(() => {
    if (!profileOpen) return;

    const onClickOutside = (event: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) {
        setProfileOpen(false);
      }
    };

    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, [profileOpen]);

  const handleLogout = () => {
    clearAuthUser();
    setProfileOpen(false);
    navigate({ to: "/login", replace: true });
  };

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col shrink-0 border-r border-border/60 bg-sidebar/60 backdrop-blur-xl transition-[width] duration-300 ease-out",
          collapsed ? "w-[72px]" : "w-64",
        )}
      >
        {/* Logo + collapse */}
        <div className="px-5 pt-6 pb-4 flex items-center justify-between">
          {!collapsed ? (
            <span className="text-xl font-bold tracking-[0.2em] text-foreground">
              RESOLVE
            </span>
          ) : (
            <div className="h-7 w-7 rounded-md bg-gradient-to-br from-electric to-mint mx-auto grid place-items-center">
              <Sparkles className="h-3.5 w-3.5 text-background" strokeWidth={2.5} />
            </div>
          )}
          <button
            onClick={() => setCollapsed((c) => !c)}
            className={cn(
              "h-7 w-7 grid place-items-center rounded-md text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors",
              collapsed && "absolute top-6 right-[-12px] z-10 bg-sidebar border border-border/60",
            )}
            aria-label="Toggle sidebar"
          >
            {collapsed ? (
              <ChevronRight className="h-3.5 w-3.5" />
            ) : (
              <ChevronLeft className="h-3.5 w-3.5" />
            )}
          </button>
        </div>

        {/* User profile */}
        {!collapsed && (
          <div className="px-4 pb-4 relative" ref={profileRef}>
            <button
              onClick={() => setProfileOpen((open) => !open)}
              className="w-full flex items-center gap-2.5 rounded-lg px-1 py-1.5 hover:bg-accent/40 transition-colors"
              type="button"
            >
              <div className="relative h-8 w-8 rounded-full bg-gradient-to-br from-mint via-electric to-mint shrink-0">
                <span className="absolute inset-0.5 rounded-full bg-background/40" />
              </div>
              <span className="text-sm font-medium text-foreground/90 truncate">
                {displayName}
              </span>
              <ChevronDown className="h-3.5 w-3.5 text-muted-foreground ml-auto" />
            </button>

            {profileOpen && (
              <div className="absolute left-4 right-4 top-[calc(100%-0.25rem)] z-50 rounded-xl border border-border/70 bg-background/95 p-2 shadow-[0_20px_60px_-20px_rgba(0,0,0,0.65)] backdrop-blur-xl">
                <div className="px-3 py-2 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                  Signed in as {authUser?.email ?? "admin@resolvemesh.local"}
                </div>
                <button
                  type="button"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-destructive transition-colors hover:bg-destructive/10"
                >
                  <LogOut className="h-4 w-4" />
                  Logout
                </button>
              </div>
            )}
          </div>
        )}

        {/* Primary nav */}
        <nav className={cn("flex-1 space-y-0.5", collapsed ? "px-2" : "px-3")}>
          {navItems.map((item) => {
            const isActive =
              item.to === "/dashboard" ? path === "/dashboard" || path.startsWith("/disputes") : path === item.to;
            const Icon = item.icon;
            return (
              <Link
                key={item.to}
                to={item.to}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "group relative flex items-center rounded-lg text-sm transition-all",
                  collapsed ? "justify-center h-10 w-10 mx-auto" : "gap-3 px-3 py-2.5",
                  isActive
                    ? "bg-gradient-to-r from-mint/20 via-electric/10 to-transparent text-foreground font-medium border border-mint/25 shadow-[0_0_24px_-8px_oklch(0.86_0.19_165/0.5)]"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent/40",
                )}
              >
                {isActive && !collapsed && (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute left-0 top-2 bottom-2 w-0.5 rounded-full bg-mint"
                    transition={{ type: "spring", stiffness: 400, damping: 32 }}
                  />
                )}
                <Icon className="h-[18px] w-[18px] shrink-0" />
                {!collapsed && (
                  <>
                    <span className="flex-1">{item.label}</span>
                    {"badge" in item && item.badge ? (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-md bg-mint/15 text-mint border border-mint/25 font-medium">
                        {item.badge}
                      </span>
                    ) : null}
                  </>
                )}
              </Link>
            );
          })}

          {!collapsed && (
            <div className="px-3 pt-3">
              <div className="flex items-center gap-2 rounded-lg border border-border/60 bg-background/40 px-2.5 py-2 text-xs text-muted-foreground">
                <Search className="h-3.5 w-3.5" />
                <span>Search cases…</span>
                <kbd className="ml-auto text-[10px] px-1.5 py-0.5 rounded bg-muted/60 border border-border/60">
                  ⌘K
                </kbd>
              </div>
            </div>
          )}
        </nav>

        {/* Upgrade card */}
        {!collapsed && (
          <div className="p-3">
            <div className="relative overflow-hidden rounded-xl p-4 bg-gradient-to-br from-mint/15 via-electric/10 to-transparent border border-mint/20">
              <div className="absolute -top-8 -right-8 h-24 w-24 rounded-full bg-mint/20 blur-2xl" />
              <div className="relative">
                <div className="text-sm font-semibold text-foreground">Go Enterprise</div>
                <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                  Unlock unlimited agents, audit exports, and SLA guarantees.
                </p>
                <button className="mt-3 w-full text-xs font-medium py-2 rounded-lg bg-foreground text-background hover:bg-foreground/90 transition-colors">
                  Upgrade
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Secondary nav */}
        <div className={cn("pb-4 space-y-0.5", collapsed ? "px-2" : "px-3")}>
          {secondaryItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.label}
                title={collapsed ? item.label : undefined}
                className={cn(
                  "flex items-center text-sm text-muted-foreground hover:text-foreground hover:bg-accent/40 rounded-lg transition-colors",
                  collapsed ? "justify-center h-10 w-10 mx-auto" : "gap-3 px-3 py-2 w-full",
                )}
              >
                <Icon className="h-[18px] w-[18px] shrink-0" />
                {!collapsed && <span>{item.label}</span>}
              </button>
            );
          })}
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        <header className="sticky top-0 z-30 h-14 border-b border-border/60 bg-background/40 backdrop-blur-xl flex items-center px-4 md:px-6 gap-3">
          <div className="md:hidden flex items-center gap-2">
            <div className="h-7 w-7 rounded-md bg-gradient-to-br from-electric to-mint" />
            <span className="text-sm font-semibold">ResolveMesh</span>
          </div>
          <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground">
            <span className="text-foreground/90 font-medium">Staff Command Center</span>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <button className="relative h-8 w-8 grid place-items-center rounded-lg border border-border/60 hover:bg-accent/50 transition-colors">
              <Bell className="h-4 w-4" />
              <span className="absolute top-1 right-1 h-1.5 w-1.5 rounded-full bg-mint" />
            </button>
            <div className="h-8 px-2.5 rounded-lg border border-border/60 flex items-center gap-2 text-xs">
              <div className="h-5 w-5 rounded-full bg-gradient-to-br from-mint to-electric" />
              <span className="hidden sm:inline">admin</span>
            </div>
          </div>
        </header>

        <main className="flex-1 min-w-0">{children}</main>
      </div>
    </div>
  );
}
