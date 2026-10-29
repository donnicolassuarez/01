import { parsearProtocolo, type Protocolo } from './protocolo';
import type { TramoId } from './tramo';

// Los protocolos son datos: se editan en assets/protocolos sin tocar el código.
 
export const PROTOCOLOS: Record<TramoId, Protocolo> = {
  '0_36': parsearProtocolo(require('../../assets/protocolos/protocolo_0_36.json')),
  '3_6': parsearProtocolo(require('../../assets/protocolos/protocolo_3_6.json')),
  '7_12': parsearProtocolo(require('../../assets/protocolos/protocolo_7_12.json')),
};
