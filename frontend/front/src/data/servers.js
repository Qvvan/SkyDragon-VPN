/**
 * servers.js - Данные о серверах VPN
 *
 * Содержит информацию о доступных серверах, их нагрузке и статусе.
 */

export const servers = [
  { id: 1, name: "Северный храм", load: 65, ping: 12, status: "online" },
  { id: 2, name: "Долина драконов", load: 38, ping: 24, status: "online" },
  { id: 3, name: "Пустыня теней", load: 91, ping: 45, status: "online" },
  { id: 4, name: "Горный пик", load: 27, ping: 18, status: "online" },
  { id: 5, name: "Забытые руины", load: 0, ping: 0, status: "offline" }
];

export default servers;