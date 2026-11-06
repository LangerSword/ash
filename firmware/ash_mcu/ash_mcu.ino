// Ash — MCU firmware (Tier 0 safety core)
// Runs on the STM32U585 under Zephyr via the Arduino core.
// The MCU owns: the loop sensor, MASTER, the monotonic counter, the wipe.
// It never returns MASTER. It answers the MPU over arduino-router.

#include <Arduino_RouterBridge.h>
#include <Arduino_LED_Matrix.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/storage/flash_map.h>
#include <cstring>

// ---------------------------------------------------------------- config
#define ASH_DEV 1                 // compile out dev hooks for submission
#define LOOP_PIN 2                // D2, INPUT_PULLUP, wire loop to GND
#define FULL_OPEN_MS 250          // Tier 0 threshold
#define AMBIG_MS 90               // shorter open -> ambiguous -> Tier 1
#define STABLE_CLOSED_MS 2000     // hold clears only after this
#define SAMPLE_MS 1

#if ASH_DEV
static bool g_sim = true;          // dev builds start with a simulated closed loop
static bool g_sim_closed = true;
#endif

static const off_t MASTER_OFF = 2080768;   // measured: storage_partition last-2 page
static const off_t COUNTER_OFF = 2072576;  // measured: storage_partition last-3 page

// ---------------------------------------------------------------- crypto (SHA-256 / HMAC)
static const uint32_t K256[64] = {
  0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
  0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
  0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
  0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
  0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
  0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
  0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
  0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};

static inline uint32_t ror32(uint32_t x, int n) { return (x >> n) | (x << (32 - n)); }

static void sha_block(uint32_t h[8], const uint8_t *p) {
  uint32_t w[64];
  for (int i = 0; i < 16; i++)
    w[i] = ((uint32_t)p[i*4] << 24) | ((uint32_t)p[i*4+1] << 16) | ((uint32_t)p[i*4+2] << 8) | p[i*4+3];
  for (int i = 16; i < 64; i++) {
    uint32_t s0 = ror32(w[i-15],7) ^ ror32(w[i-15],18) ^ (w[i-15] >> 3);
    uint32_t s1 = ror32(w[i-2],17) ^ ror32(w[i-2],19) ^ (w[i-2] >> 10);
    w[i] = w[i-16] + s0 + w[i-7] + s1;
  }
  uint32_t a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],h7=h[7];
  for (int i = 0; i < 64; i++) {
    uint32_t S1 = ror32(e,6) ^ ror32(e,11) ^ ror32(e,25);
    uint32_t ch = (e & f) ^ (~e & g);
    uint32_t t1 = h7 + S1 + ch + K256[i] + w[i];
    uint32_t S0 = ror32(a,2) ^ ror32(a,13) ^ ror32(a,22);
    uint32_t mj = (a & b) ^ (a & c) ^ (b & c);
    uint32_t t2 = S0 + mj;
    h7=g; g=f; f=e; e=d+t1; d=c; c=b; b=a; a=t1+t2;
  }
  h[0]+=a; h[1]+=b; h[2]+=c; h[3]+=d; h[4]+=e; h[5]+=f; h[6]+=g; h[7]+=h7;
}

static void sha256(const uint8_t *d, size_t n, uint8_t out[32]) {
  uint32_t h[8] = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                   0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
  uint8_t buf[256];
  memset(buf, 0, sizeof buf);
  if (n > 190) n = 190;
  memcpy(buf, d, n);
  buf[n] = 0x80;
  size_t total = ((n + 9 + 63) / 64) * 64;
  uint64_t bits = (uint64_t)n * 8;
  for (int i = 0; i < 8; i++) buf[total - 1 - i] = (uint8_t)(bits >> (8 * i));
  for (size_t off = 0; off < total; off += 64) sha_block(h, buf + off);
  for (int i = 0; i < 8; i++) {
    out[i*4]   = (uint8_t)(h[i] >> 24);
    out[i*4+1] = (uint8_t)(h[i] >> 16);
    out[i*4+2] = (uint8_t)(h[i] >> 8);
    out[i*4+3] = (uint8_t)h[i];
  }
}

static void hmac_sha256(const uint8_t *key, size_t klen,
                        const uint8_t *msg, size_t mlen, uint8_t out[32]) {
  uint8_t k[64]; memset(k, 0, sizeof k);
  if (klen > 64) sha256(key, klen, k); else memcpy(k, key, klen);
  uint8_t ipad[64], opad[64];
  for (int i = 0; i < 64; i++) { ipad[i] = k[i] ^ 0x36; opad[i] = k[i] ^ 0x5c; }
  uint8_t inner[32], buf[256];
  memcpy(buf, ipad, 64); memcpy(buf + 64, msg, mlen);
  sha256(buf, 64 + mlen, inner);
  memcpy(buf, opad, 64); memcpy(buf + 64, inner, 32);
  sha256(buf, 96, out);
}

static void hex(const uint8_t *b, size_t n, char *out) {
  static const char *H = "0123456789abcdef";
  for (size_t i = 0; i < n; i++) { out[i*2] = H[b[i] >> 4]; out[i*2+1] = H[b[i] & 15]; }
  out[n*2] = 0;
}

// ---------------------------------------------------------------- flash
static const struct device *g_flash;
static bool g_synced = false;

static bool flash_ready() {
  if (g_synced) return true;
  g_flash = FIXED_PARTITION_DEVICE(storage_partition);
  g_synced = device_is_ready(g_flash);
  return g_synced;
}

static bool page_is_blank(off_t off) {
  uint8_t b[32];
  for (int i = 0; i < 4; i++) {
    if (flash_read(g_flash, off + i*32, b, sizeof b) != 0) return false;
    for (size_t j = 0; j < sizeof b; j++) if (b[j] != 0xFF) return false;
  }
  return true;
}

static uint32_t g_counter = 0;
static uint8_t g_master[32];
static bool g_master_ok = false;

static bool load_master() {
  if (!flash_ready()) return false;
  if (page_is_blank(MASTER_OFF)) return false;
  return flash_read(g_flash, MASTER_OFF, g_master, sizeof g_master) == 0;
}

static bool provision_master() {
  // Dev-grade entropy: ADC noise + micros. Replace with a TRNG before any real use.
  for (int i = 0; i < 32; i++) {
    uint32_t t = micros() ^ (analogRead(A0) << 7) ^ (i * 2654435761u);
    g_master[i] = (uint8_t)(t ^ (t >> 8) ^ (t >> 16));
    delay(1);
  }
  if (flash_erase(g_flash, MASTER_OFF, 8192) != 0) return false;
  if (flash_write(g_flash, MASTER_OFF, g_master, sizeof g_master) != 0) return false;
  uint8_t rb[32];
  if (flash_read(g_flash, MASTER_OFF, rb, sizeof rb) != 0) return false;
  return memcmp(rb, g_master, sizeof rb) == 0;
}

static void wipe(const char *reason) {
  uint8_t flag = 0xA5;
  flash_erase(g_flash, COUNTER_OFF, 8192);
  flash_write(g_flash, COUNTER_OFF, &flag, 1);

  flash_erase(g_flash, MASTER_OFF, 8192);
  bool blank = page_is_blank(MASTER_OFF);
  memset(g_master, 0, sizeof g_master);
  g_master_ok = false;

  flag = 0x00;
  flash_write(g_flash, COUNTER_OFF, &flag, 1);
  uint32_t c = ++g_counter;
  flash_write(g_flash, COUNTER_OFF + 8, &c, sizeof c);

  Bridge.notify("ev_tamper", String(reason), blank ? 1 : 0, (int)c);
}

// ---------------------------------------------------------------- state
enum { ST_ARMED = 1, ST_UNSEALED = 2, ST_TAMPERED = 3 };
static int g_state = ST_ARMED;
static uint8_t g_nonce[32];
static char g_container[24] = "C-001";

// ---------------------------------------------------------------- LED
Arduino_LED_Matrix matrix;

// ---------------------------------------------------------------- animation
enum { AN_BOOT, AN_ARMED, AN_AMBER, AN_WIPE, AN_TAMPER, AN_UNSEALED };
static int g_anim = AN_BOOT;
static uint32_t g_anim_start = 0;

static bool g_amber = false;
static bool g_hold = false;
static uint32_t g_deadline_ms = 5000;
static uint32_t g_deadline_at = 0;
static uint32_t g_closed_since = 0;

static void led(bool r, bool g, bool b) {
  pinMode(LED3_R, OUTPUT); pinMode(LED3_G, OUTPUT); pinMode(LED3_B, OUTPUT);
  digitalWrite(LED3_R, r); digitalWrite(LED3_G, g); digitalWrite(LED3_B, b);
}
static void set_anim(int a) { g_anim = a; g_anim_start = millis(); }

static void anim_frame(uint8_t f[104], uint32_t now) {
  uint32_t t = now - g_anim_start;
  memset(f, 0, 104);
  switch (g_anim) {
    case AN_BOOT: {
      int x = (int)((t / 55) % 13);
      for (int r = 0; r < 8; r++) f[r*13 + x] = 1;
      led(false, false, true); break;
    }
    case AN_ARMED: {
      int phase = (int)((t / 500) % 8);
      int lvl = phase < 4 ? phase + 1 : 8 - phase;
      for (int r = 0; r < lvl; r++) for (int c = 0; c < 13; c++) f[r*13 + c] = 1;
      led(false, true, false); break;
    }
    case AN_AMBER: {
      uint32_t left = g_deadline_at > now ? g_deadline_at - now : 0;
      int bars = (int)((left * 13) / (g_deadline_ms ? g_deadline_ms : 1));
      if (bars > 13) bars = 13;
      for (int c = 13 - bars; c < 13; c++) for (int r = 0; r < 8; r++) f[r*13 + c] = 1;
      bool on = ((t / 250) % 2) == 0;
      led(on, on, false); break;
    }
    case AN_WIPE: {
      for (int i = 0; i < 26; i++) f[(i * 7 + (int)(t / 40)) % 104] = 1;
      led(true, false, false); break;
    }
    case AN_TAMPER: {
      if (((t / 400) % 2) == 0)
        for (int i = 0; i < 8; i++) { f[i*13 + i] = 1; f[i*13 + (7 - i)] = 1; }
      led(true, false, false); break;
    }
    case AN_UNSEALED: {
      for (int i = 0; i < 8; i++) { f[i*13 + i] = 1; f[i*13 + (12 - i)] = 1; }
      led(false, true, false); break;
    }
  }
}

// ---------------------------------------------------------------- bridge
static String st_json() {
  char b[96];
  snprintf(b, sizeof b, "{\"state\":%d,\"counter\":%u,\"master\":%d,\"loop\":%d}",
           g_state, (unsigned)g_counter, g_master_ok ? 1 : 0,
           digitalRead(LOOP_PIN) == HIGH ? 1 : 0, g_amber ? 1 : 0);
  return String(b);
}

String arm_impl() {
  if (g_state == ST_TAMPERED) return st_json();
  if (!g_master_ok) {
    if (!provision_master()) return String("{\"error\":\"provision_failed\"}");
    g_master_ok = true;
  }
  g_state = ST_ARMED;
  g_amber = false; g_hold = false;
  set_anim(AN_ARMED);
  return st_json();
}

String status_impl() { return st_json(); }

String derive_impl(String nonce_hex) {
  if (g_state != ST_ARMED || !g_master_ok) return String("ERR:not_armed");
  uint8_t msg[64];
  size_t n = nonce_hex.length() / 2;
  if (n > 32) n = 32;
  for (size_t i = 0; i < n; i++)
    msg[i] = (uint8_t)strtoul(nonce_hex.substring(i * 2, i * 2 + 2).c_str(), nullptr, 16);
  size_t cl = strlen(g_container);
  memcpy(msg + n, g_container, cl);
  uint8_t out[32]; char hx[65];
  hmac_sha256(g_master, 32, msg, n + cl, out);
  hex(out, 32, hx);
  memset(out, 0, sizeof out);
  return String(hx);
}

String selftest_impl() {
  uint8_t d[32]; char hx[65];
  sha256((const uint8_t *)"abc", 3, d); hex(d, 32, hx);
  bool ok1 = strcmp(hx, "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad") == 0;
  uint8_t m[32];
  hmac_sha256((const uint8_t *)"Jefe", 4, (const uint8_t *)"what do ya want for nothing?", 28, m);
  hex(m, 32, hx);
  bool ok2 = strcmp(hx, "5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843") == 0;
  return String(ok1 && ok2 ? "ok" : (ok1 ? "sha_ok_hmac_bad" : "sha_bad"));
}

String decision_impl(String verdict) {
  if (!g_amber) return st_json();
  if (verdict == "wipe") {
    wipe("0g");
    g_state = ST_TAMPERED;
    g_amber = false;
    set_anim(AN_TAMPER);
    return st_json();
  }
  g_hold = true;
  return st_json();
}

String deadline_impl(int ms) {
  if (ms < 1000) ms = 1000;
  if (ms > 8000) ms = 8000;
  g_deadline_ms = (uint32_t)ms;
  return st_json();
}

#if ASH_DEV
String sim_impl(int closed) { g_sim = true; g_sim_closed = (closed != 0); return st_json(); }
String reprovision_impl() {
  flash_erase(g_flash, MASTER_OFF, 8192);
  flash_erase(g_flash, COUNTER_OFF, 8192);
  g_counter = 0; g_master_ok = false; g_state = ST_ARMED;
  provision_master();
  g_master_ok = true;
  set_anim(AN_ARMED);
  return st_json();
}
#endif

void setup() {
  matrix.begin(); matrix.setGrayscaleBits(1); matrix.clear();
  set_anim(AN_BOOT);
  Bridge.begin();

  Bridge.provide("arm", arm_impl);
  Bridge.provide("status", status_impl);
  Bridge.provide("derive", derive_impl);
  Bridge.provide("selftest", selftest_impl);
  Bridge.provide("decision", decision_impl);
  Bridge.provide("deadline", deadline_impl);
#if ASH_DEV
  Bridge.provide("sim", sim_impl);
  Bridge.provide("reprovision", reprovision_impl);
#endif

  if (!flash_ready()) { led(true, false, false); return; }

  // wipe-pending recovery: a set flag means finish the wipe before anything else
  uint8_t flag = 0xFF;
  flash_read(g_flash, COUNTER_OFF, &flag, 1);
  if (flag == 0xA5) { wipe("pending"); g_state = ST_TAMPERED; set_anim(AN_TAMPER); return; }

  flash_read(g_flash, COUNTER_OFF + 8, &g_counter, sizeof g_counter);
  if (g_counter == 0xFFFFFFFFu) { g_counter = 0; flash_write(g_flash, COUNTER_OFF + 8, &g_counter, sizeof g_counter); }
  g_master_ok = load_master();
  if (g_master_ok) { g_state = ST_ARMED; set_anim(AN_ARMED); }
}

static uint32_t last_sample = 0, open_since = 0, last_frame = 0;
static uint32_t last_open_ms = 0, last_edge = 0;
static int edge_count = 0;

static void start_amber(uint32_t now) {
  g_amber = true;
  g_hold = false;
  g_deadline_at = now + g_deadline_ms;
  g_closed_since = now;
  set_anim(AN_AMBER);
  char feat[176];
  snprintf(feat, sizeof feat,
           "{\"edges\":%d,\"open_ms\":%u,\"since_arm_ms\":%u,\"counter\":%u,"
           "\"policy\":\"strict\",\"deadline_ms\":%u}",
           edge_count, (unsigned)last_open_ms, (unsigned)now,
           (unsigned)g_counter, (unsigned)g_deadline_ms);
  Bridge.notify("ev_ambiguous", String(feat));
}

void loop() {
  uint32_t now = millis();

  if (now - last_frame >= 33) {          // 30 fps, never blocks sampling
    last_frame = now;
    uint8_t f[104];
    anim_frame(f, now);
    matrix.draw(f);
  }

  if (g_state != ST_ARMED) { delay(2); return; }

  if (now - last_sample >= SAMPLE_MS) {
    last_sample = now;
#if ASH_DEV
    bool open = g_sim ? !g_sim_closed : (digitalRead(LOOP_PIN) == HIGH);
#else
    bool open = digitalRead(LOOP_PIN) == HIGH;
#endif

    if (open) {
      if (!open_since) { open_since = now; last_edge = now; edge_count++; }
      if (now - open_since >= FULL_OPEN_MS) {
        wipe("open");
        g_state = ST_TAMPERED;
        g_amber = false;
        set_anim(AN_TAMPER);
        return;
      }
    } else {
      if (open_since) {
        last_open_ms = now - open_since;
        open_since = 0;
        if (last_open_ms >= AMBIG_MS && !g_amber) start_amber(now);
      }
      if (g_amber) {
        if (!g_closed_since) g_closed_since = now;
        if (g_hold && now - g_closed_since >= STABLE_CLOSED_MS) {
          g_amber = false; g_hold = false;
          set_anim(AN_ARMED);
          Bridge.notify("ev_hold", String("cleared"), (int)g_counter);
        }
      }
    }

    if (edge_count >= 6 && !g_amber) start_amber(now);
    if (now - last_edge > 500) edge_count = 0;

    if (g_amber && (int32_t)(now - g_deadline_at) >= 0) {
      wipe("0g_timeout");
      g_state = ST_TAMPERED;
      g_amber = false;
      set_anim(AN_TAMPER);
    }
  }
}
