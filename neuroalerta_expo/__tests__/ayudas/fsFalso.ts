 
// Reemplazo de expo-file-system respaldado por el disco real de Node, para probar la lógica de archivos.
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

type Parte = string | { uri: string };
const unir = (partes: Parte[]) =>
  partes
    .map((p, i) => {
      const t = typeof p === 'string' ? p : p.uri;
      return i === 0 ? t : t.replace(/^\/+/, '');
    })
    .join('/')
    .replace(/\/{2,}/g, '/');

export class File {
  uri: string;
  constructor(...partes: Parte[]) {
    this.uri = unir(partes);
  }
  get exists() {
    return fs.existsSync(this.uri);
  }
  get extension() {
    return path.extname(this.uri);
  }
  create() {
    fs.writeFileSync(this.uri, '');
  }
  write(contenido: string) {
    fs.writeFileSync(this.uri, contenido);
  }
  async copy(destino: File) {
    fs.copyFileSync(this.uri, destino.uri);
  }
  delete() {
    fs.rmSync(this.uri);
  }
}

export class Directory {
  uri: string;
  constructor(...partes: Parte[]) {
    this.uri = unir(partes);
  }
  get exists() {
    return fs.existsSync(this.uri);
  }
  create() {
    fs.mkdirSync(this.uri, { recursive: true });
  }
}

export const Paths = { document: new Directory(os.tmpdir()), cache: new Directory(os.tmpdir()) };
