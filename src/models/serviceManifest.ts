import { LivetimingVersion } from "./livetimingVersion";

export interface ServiceManifest {
  colSpec: string[][]
  description: string
  livetimingVersion: LivetimingVersion
  name: string
  pollInteval: number
  serviceClass: string
  source: string[]
  trackDataSpec: string[]
  uuid: string
}