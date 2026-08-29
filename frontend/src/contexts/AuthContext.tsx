import { useEffect, useState, type ReactNode } from 'react'
import type { Session } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'
import { AuthContext, type AuthContextValue } from './auth-context'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Guard against this resolving after the effect has been cleaned up (React 18
    // StrictMode double-invokes effects in dev) — a late resolution here must not
    // overwrite a session set in the meantime by signIn/signUp or a real auth event.
    let active = true

    supabase.auth.getSession().then(({ data }) => {
      if (!active) return
      // Only apply this if nothing else (signIn/signUp, or a real auth event) has
      // already set a session while this call was in flight — otherwise this stale
      // result would silently clobber a session that's already correct.
      setSession((current) => current ?? data.session)
      setLoading(false)
    })

    const { data: listener } = supabase.auth.onAuthStateChange((_event, newSession) => {
      if (active) setSession(newSession)
    })

    return () => {
      active = false
      listener.subscription.unsubscribe()
    }
  }, [])

  async function signUp(email: string, password: string) {
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (!error && data.session) {
      // Set synchronously — onAuthStateChange fires asynchronously, and callers that
      // navigate right after this resolves would otherwise race ahead of it.
      setSession(data.session)
    }
    return { error: error?.message ?? null }
  }

  async function signIn(email: string, password: string) {
    const { data, error } = await supabase.auth.signInWithPassword({ email, password })
    if (!error) {
      setSession(data.session)
    }
    return { error: error?.message ?? null }
  }

  async function signOut() {
    await supabase.auth.signOut()
  }

  async function requestPasswordReset(email: string) {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    })
    return { error: error?.message ?? null }
  }

  async function updatePassword(newPassword: string) {
    const { error } = await supabase.auth.updateUser({ password: newPassword })
    return { error: error?.message ?? null }
  }

  const value: AuthContextValue = {
    session,
    loading,
    signUp,
    signIn,
    signOut,
    requestPasswordReset,
    updatePassword,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
