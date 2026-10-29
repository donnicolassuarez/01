import type { NivelOrientacion } from '../domain/protocolo';

export interface TextoNivel {
  titulo: string;
  resumen: string;
  paso: string;
}

export interface Consentimiento {
  version: string;
  titulo: string;
  texto: string[];
  seGuarda: string[];
  privacidad: string[];
  aceptacion: string;
}

export interface TextosApp {
  aviso: string;
  niveles: Record<NivelOrientacion, TextoNivel>;
  focoGrave: string;
  notaNoSe: string;
  notaPocasRespuestas: string;
  consentimiento: Consentimiento;
}

type Json = Record<string, any>;  

/** Convierte los JSON de textos editables en un objeto tipado. */
export function parsearTextos(niveles: Json, consentimiento: Json): TextosApp {
  const nivel = (id: NivelOrientacion): TextoNivel => ({
    titulo: niveles.niveles[id].titulo,
    resumen: niveles.niveles[id].resumen,
    paso: niveles.niveles[id].paso,
  });
  return {
    aviso: niveles.aviso,
    niveles: {
      sin_senales: nivel('sin_senales'),
      comentar_control: nivel('comentar_control'),
      consultar_pronto: nivel('consultar_pronto'),
    },
    focoGrave: niveles.foco_grave,
    notaNoSe: niveles.nota_no_se,
    notaPocasRespuestas: niveles.nota_pocas_respuestas,
    consentimiento: {
      version: consentimiento.version,
      titulo: consentimiento.titulo,
      texto: consentimiento.texto,
      seGuarda: consentimiento.se_guarda,
      privacidad: consentimiento.privacidad,
      aceptacion: consentimiento.aceptacion,
    },
  };
}

 
export const TEXTOS: TextosApp = parsearTextos(
  require('../../assets/textos/niveles.json'),
  require('../../assets/textos/consentimiento.json'),
);
