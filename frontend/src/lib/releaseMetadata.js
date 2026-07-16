export const RELEASE_METADATA = Object.freeze({
  contract_version: '2.0',
  assessment_version: 'india-en-3.0.0',
  scoring_policy_version: 'readiness-rubric-1.0.0',
});

const viteEnv = typeof import.meta.env === "object" && import.meta.env !== null
  ? import.meta.env
  : {};
const configuredReleaseSha = viteEnv.VITE_RELEASE_SHA;

export const FRONTEND_RELEASE_SHA = (configuredReleaseSha || 'local').trim() || 'local';

const isProductionBuild = viteEnv.MODE === 'production';
if (isProductionBuild && !/^[0-9a-f]{40}$/.test(FRONTEND_RELEASE_SHA)) {
  throw new Error('VITE_RELEASE_SHA must be the exact 40-character release commit SHA.');
}

export function isMatchingReleaseMetadata(value) {
  return value !== null
    && typeof value === 'object'
    && !Array.isArray(value)
    && value.contract_version === RELEASE_METADATA.contract_version
    && value.assessment_version === RELEASE_METADATA.assessment_version
    && value.scoring_policy_version === RELEASE_METADATA.scoring_policy_version
    && value.release_sha === FRONTEND_RELEASE_SHA;
}
