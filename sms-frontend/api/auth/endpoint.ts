import { public_api_url } from "@/api/consts";

export const AUTH_API = `${public_api_url}/auth`;
export const USERS_API = `${AUTH_API}/users`;

export const AUTH_ENDPOINTS = {
    LOGIN: `${AUTH_API}/login`,
    REFRESH: `${AUTH_API}/refresh`,
    LOGOUT: `${AUTH_API}/logout`,
    ME: `${AUTH_API}/me`,
};

export const USER_ENDPOINTS = {
    LIST: USERS_API,
    CREATE: USERS_API,
    READ: (id: string) => `${USERS_API}/${id}`,
    UPDATE: (id: string) => `${USERS_API}/${id}`,
    DELETE: (id: string) => `${USERS_API}/${id}`,
};
