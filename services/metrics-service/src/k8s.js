const k8s = require('@kubernetes/client-node');

const kc = new k8s.KubeConfig();
try {
  kc.loadFromCluster();
} catch {
  kc.loadFromDefault();
}
const coreV1 = kc.makeApiClient(k8s.CoreV1Api);

async function getPods() {
  try {
    const res = await coreV1.listPodForAllNamespaces();
    return (res.body.items || []).map(pod => {
      const container = pod.spec?.containers?.[0] || {};
      const status    = pod.status?.phase || 'Unknown';
      const startTime = pod.status?.startTime;
      const age       = startTime
        ? Math.floor((Date.now() - new Date(startTime).getTime()) / 1000)
        : 0;
      const restarts  = pod.status?.containerStatuses?.[0]?.restartCount || 0;
      return {
        name:     pod.metadata?.name || 'unknown',
        service:  pod.metadata?.labels?.app || pod.metadata?.name || 'unknown',
        status,
        cpu:      container.resources?.requests?.cpu || 'n/a',
        memory:   container.resources?.requests?.memory || 'n/a',
        restarts,
        age
      };
    });
  } catch (err) {
    console.error('[k8s] getPods error:', err.message);
    return [];
  }
}

module.exports = { getPods };
