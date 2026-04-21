import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(_request: NextRequest) {
  // La protection des routes est gérée côté client via AuthContext et useRequireAuth hook
  // Pour un vrai middleware au serveur, utiliser des cookies httpOnly au lieu de localStorage

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|api).*)'],
}
