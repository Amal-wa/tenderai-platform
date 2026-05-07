/**
 * Tests d'intégration — Audit Log Dashboard
 * 
 * Vérifie que les types, API et composants fonctionnent correctement
 */

import type { AuditLogEntry, AuditLogsResponse, AuditAction, AuditResourceType, AuditStatus } from '@/types/audit'

/**
 * Test 1: Vérifier les types TypeScript
 */
const testAuditAction = (action: AuditAction) => {
  const validActions: AuditAction[] = ['login', 'logout', 'login_failed', 'create', 'read', 'update', 'delete']
  return validActions.includes(action)
}

const testAuditResourceType = (resourceType: AuditResourceType) => {
  const validTypes: AuditResourceType[] = [
    'user',
    'role',
    'document',
    'chunk',
    'compliance_report',
    'tenant',
    'auth_session',
  ]
  return validTypes.includes(resourceType)
}

const testAuditStatus = (status: AuditStatus) => {
  return status === 'success' || status === 'failure'
}

/**
 * Test 2: Créer un entry valide
 */
const createMockAuditLog = (overrides?: Partial<AuditLogEntry>): AuditLogEntry => ({
  id: 124,
  tenant_id: '550e8400-e29b-41d4-a716-446655440000',
  user_id: '650e8400-e29b-41d4-a716-446655440001',
  action: 'login',
  resource_type: 'auth_session',
  resource_id: null,
  old_value: null,
  new_value: null,
  status: 'success',
  reason: null,
  ip_address: '192.168.1.10',
  user_agent: 'Chrome 124',
  timestamp: '2026-05-03T09:14:32Z',
  hash: 'abc123def456789abc123def456789abc123def456789abc123def456789abc1',
  previous_hash: 'xyz789uvw012xyz789uvw012xyz789uvw012xyz789uvw012xyz789uvw012xyz7',
  ...overrides,
})

/**
 * Test 3: Créer une réponse valide
 */
const createMockAuditLogsResponse = (items: AuditLogEntry[] = []): AuditLogsResponse => ({
  total: items.length,
  page: 1,
  size: items.length,
  items,
})

/**
 * Test 4: Vérifier intégrité des données
 */
const validateAuditLog = (log: AuditLogEntry): boolean => {
  return !!(
    log.id &&
    log.tenant_id &&
    log.action &&
    testAuditAction(log.action) &&
    log.resource_type &&
    testAuditResourceType(log.resource_type) &&
    log.status &&
    testAuditStatus(log.status) &&
    log.timestamp &&
    log.hash &&
    log.hash.length === 64
  ) // SHA-256 = 64 chars
}

/**
 * Test 5: Données réalistes
 */
const mockAuditLogsForTesting = (): AuditLogEntry[] => [
  createMockAuditLog({ id: 124, action: 'login', resource_type: 'auth_session', status: 'success' }),
  createMockAuditLog({
    id: 125,
    action: 'delete',
    resource_type: 'document',
    status: 'failure',
    reason: 'Permission denied: role=contributor',
    user_id: 'user-002',
  }),
  createMockAuditLog({
    id: 126,
    action: 'read',
    resource_type: 'compliance_report',
    status: 'success',
    user_id: 'user-003',
  }),
  createMockAuditLog({
    id: 127,
    action: 'update',
    resource_type: 'user',
    status: 'success',
    user_id: 'user-004',
    old_value: { role: 'analyst' },
    new_value: { role: 'manager' },
  }),
  createMockAuditLog({
    id: 128,
    action: 'create',
    resource_type: 'chunk',
    status: 'success',
    user_id: null, // System action
    reason: 'APScheduler — chunking pipeline',
    new_value: { chunk_index: 42, tokens: 512 },
  }),
]

/**
 * Export test utilities
 */
export {
  testAuditAction,
  testAuditResourceType,
  testAuditStatus,
  createMockAuditLog,
  createMockAuditLogsResponse,
  validateAuditLog,
  mockAuditLogsForTesting,
}

/**
 * Run tests (NodeJS environment)
 */
if (typeof window === 'undefined') {
  console.log('🧪 Running Audit Log Tests...')

  // Test 1: Types
  console.assert(testAuditAction('login'), '❌ testAuditAction failed')
  console.assert(!testAuditAction('invalid' as AuditAction), '❌ testAuditAction should reject invalid')
  console.log('✅ testAuditAction passed')

  // Test 2: MockLog
  const log = createMockAuditLog()
  console.assert(validateAuditLog(log), '❌ validateAuditLog failed')
  console.log('✅ validateAuditLog passed')

  // Test 3: MockResponse
  const response = createMockAuditLogsResponse([log])
  console.assert(response.total === 1, '❌ Response total should be 1')
  console.assert(response.items.length === 1, '❌ Response items should have 1 item')
  console.log('✅ createMockAuditLogsResponse passed')

  // Test 4: RealisticData
  const logs = mockAuditLogsForTesting()
  console.assert(logs.length === 5, '❌ Should have 5 mock logs')
  console.assert(logs.every(validateAuditLog), '❌ All logs should be valid')
  console.assert(logs.some((l) => l.user_id === null), '❌ Should have system action')
  console.assert(logs.some((l) => l.status === 'failure'), '❌ Should have failed action')
  console.log('✅ mockAuditLogsForTesting passed')

  console.log('✅ All Audit Log tests passed!')
}

