/**
 * Password generation composable — pure functions for random and deterministic passwords.
 *
 * All cryptographic operations use browser-native APIs:
 * - `crypto.getRandomValues()` for random password generation (CSPRNG)
 * - `crypto.subtle.digest('SHA-256', ...)` for deterministic password generation
 *
 * No data leaves the browser — zero server-side processing.
 */

// Character sets for password generation
const CHARSETS = {
  uppercase: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  lowercase: 'abcdefghijklmnopqrstuvwxyz',
  digits: '0123456789',
  symbols: '!@#$%^&*()_+-=[]{}|;:,.<>?'
};

// Ambiguous characters that are hard to distinguish visually
const AMBIGUOUS = 'il1IO0';

export interface PasswordGenOptions {
  uppercase: boolean;
  lowercase: boolean;
  digits: boolean;
  symbols: boolean;
  excludeAmbiguous: boolean;
}

/**
 * Build the character pool based on selected options.
 */
export function buildPool(options: PasswordGenOptions): string {
  let pool = '';
  if (options.uppercase) pool += CHARSETS.uppercase;
  if (options.lowercase) pool += CHARSETS.lowercase;
  if (options.digits) pool += CHARSETS.digits;
  if (options.symbols) pool += CHARSETS.symbols;

  if (options.excludeAmbiguous) {
    pool = pool.split('').filter(c => !AMBIGUOUS.includes(c)).join('');
  }

  return pool;
}

/**
 * Calculate entropy in bits: L × log₂(q)
 * where L = length, q = pool size.
 */
export function calculateEntropy(length: number, poolSize: number): number {
  if (poolSize === 0) return 0;
  return length * Math.log2(poolSize);
}

/**
 * Secure random number in [0, max) using rejection sampling to eliminate modulo bias.
 */
function secureRandom(max: number): number {
  const array = new Uint32Array(1);
  const limit = Math.floor(0x100000000 / max) * max;
  let value: number;

  do {
    crypto.getRandomValues(array);
    value = array[0];
  } while (value >= limit);

  return value % max;
}

/**
 * Generate a random password with constraints:
 * - At least one character from each selected class (if enabled)
 * - Remaining positions filled from the full pool
 * - Uses Fisher-Yates shuffle for position assignment
 */
export function generateRandomPassword(
  length: number,
  pool: string,
  selectedClasses: Record<string, boolean>,
  excludeAmbiguous: boolean
): string {
  const password = new Array<string>(length);
  const positions = Array.from({ length }, (_, i) => i);

  // Fisher-Yates shuffle for deterministic position assignment
  for (let i = positions.length - 1; i > 0; i--) {
    const j = secureRandom(i + 1);
    [positions[i], positions[j]] = [positions[j], positions[i]];
  }

  // Place at least one character from each selected class
  let posIdx = 0;
  for (const [className, enabled] of Object.entries(selectedClasses)) {
    if (!enabled) continue;

    let charset = CHARSETS[className as keyof typeof CHARSETS];
    if (excludeAmbiguous) {
      charset = charset.split('').filter(c => !AMBIGUOUS.includes(c)).join('');
    }
    if (charset.length === 0) continue;

    const pos = positions[posIdx++];
    password[pos] = charset[secureRandom(charset.length)];
  }

  // Fill remaining positions from the full pool
  for (let i = 0; i < length; i++) {
    if (password[i] === undefined) {
      password[i] = pool[secureRandom(pool.length)];
    }
  }

  return password.join('');
}

/**
 * Extend hash output to arbitrary length by hashing with counter.
 * Input: `data:0`, `data:1`, ... concatenated.
 */
async function hashToBytes(data: string, numBytes: number): Promise<Uint8Array> {
  const encoder = new TextEncoder();
  const bytes: number[] = [];
  let counter = 0;

  while (bytes.length < numBytes) {
    const input = encoder.encode(data + ':' + counter);
    const hashBuffer = await crypto.subtle.digest('SHA-256', input);
    const hashArray = new Uint8Array(hashBuffer);
    bytes.push(...hashArray);
    counter++;
  }

  return new Uint8Array(bytes.slice(0, numBytes));
}

/**
 * Generate a deterministic (reproducible) password from name + salt + length.
 * Same inputs always produce the same output.
 *
 * Algorithm:
 * 1. Hash `name + salt + length` with SHA-256, extend to `length` bytes
 * 2. Use hash bytes to shuffle positions (deterministic Fisher-Yates)
 * 3. Place one character from each selected class at shuffled positions
 * 4. Fill remaining positions from the pool using hash bytes
 */
export async function generateDeterministicPassword(
  name: string,
  salt: string,
  length: number,
  pool: string,
  selectedClasses: Record<string, boolean>,
  excludeAmbiguous: boolean
): Promise<string> {
  const data = name + salt + length;
  const hashBytes = await hashToBytes(data, length);
  const password = new Array<string>(length);
  const positions = Array.from({ length }, (_, i) => i);

  // Deterministic shuffle using hash bytes
  for (let i = positions.length - 1; i > 0; i--) {
    const j = hashBytes[i] % (i + 1);
    [positions[i], positions[j]] = [positions[j], positions[i]];
  }

  // Place at least one character from each selected class
  let posIdx = 0;
  for (const [className, enabled] of Object.entries(selectedClasses)) {
    if (!enabled) continue;

    let charset = CHARSETS[className as keyof typeof CHARSETS];
    if (excludeAmbiguous) {
      charset = charset.split('').filter(c => !AMBIGUOUS.includes(c)).join('');
    }
    if (charset.length === 0) continue;

    const pos = positions[posIdx++];
    const byteVal = hashBytes[pos];
    password[pos] = charset[byteVal % charset.length];
  }

  // Fill remaining positions from the pool
  for (let i = 0; i < length; i++) {
    if (password[i] === undefined) {
      const byteVal = hashBytes[i];
      password[i] = pool[byteVal % pool.length];
    }
  }

  return password.join('');
}
