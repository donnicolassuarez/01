// Configuración dinámica: parte de app.json y, si se pide, quita el permiso de internet (versión final sin conexión).
// Uso: SIN_INTERNET=1 npx expo prebuild --clean   (o la variable en el perfil de EAS)
module.exports = ({ config }) => {
  const bloqueados = new Set(config.android?.blockedPermissions ?? []);
  if (process.env.SIN_INTERNET === '1') bloqueados.add('android.permission.INTERNET');
  return { ...config, android: { ...config.android, blockedPermissions: [...bloqueados] } };
};
