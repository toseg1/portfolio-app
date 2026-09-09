const fs = require("fs");
const path = require("path");

const localesDir = path.join(__dirname, "..", "locales");
const [frDir, enDir] = ["fr", "en"].map((locale) => path.join(localesDir, locale));

function keysOf(obj, prefix = "") {
  return Object.entries(obj).flatMap(([key, value]) => {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    return typeof value === "object" && value !== null
      ? keysOf(value, fullKey)
      : [fullKey];
  });
}

const namespaces = fs.readdirSync(frDir).filter((f) => f.endsWith(".json"));
let hasMismatch = false;

for (const namespace of namespaces) {
  const frPath = path.join(frDir, namespace);
  const enPath = path.join(enDir, namespace);

  if (!fs.existsSync(enPath)) {
    console.error(`Missing en/${namespace} (present in fr/${namespace})`);
    hasMismatch = true;
    continue;
  }

  const frKeys = keysOf(JSON.parse(fs.readFileSync(frPath, "utf8"))).sort();
  const enKeys = keysOf(JSON.parse(fs.readFileSync(enPath, "utf8"))).sort();

  const missingInEn = frKeys.filter((k) => !enKeys.includes(k));
  const missingInFr = enKeys.filter((k) => !frKeys.includes(k));

  if (missingInEn.length || missingInFr.length) {
    hasMismatch = true;
    console.error(`Key mismatch in ${namespace}:`);
    if (missingInEn.length) console.error(`  missing in en: ${missingInEn.join(", ")}`);
    if (missingInFr.length) console.error(`  missing in fr: ${missingInFr.join(", ")}`);
  }
}

if (hasMismatch) {
  process.exit(1);
}

console.log("Locale key parity OK");
