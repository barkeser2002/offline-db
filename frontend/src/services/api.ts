import axios from 'axios';

// Create Axios client with base URL
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // In a real app, getting token might be async or from a store/cookie
    // For now, we'll try to get it from localStorage if we were client-side
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('accessToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle token refresh (simplified)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If error is 401 and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refreshToken');
        if (refreshToken) {
          const { data } = await axios.post('http://localhost:8000/api/token/refresh/', {
            refresh: refreshToken,
          });
          
          localStorage.setItem('accessToken', data.access);
          originalRequest.headers.Authorization = `Bearer ${data.access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed, logout user
        if (typeof window !== 'undefined') {
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// API Service Interfaces & Methods
export interface Anime {
  id: number;
  mal_id: number;
  title: string;
  cover_image: string;
  score: string;
  type: string;
  date_aired: string;
  status: string;
  rating: string;
  genres: { id: number; name: string; slug: string }[];
}

export interface Episode {
  id: number;
  title: string;
  number: number;
  cover_image: string;
  duration: string;
  aired_date: string;
  season?: { anime: { title: string; id: number } };
}

export interface HomeData {
  trending: Anime[];
  latest_episodes: Episode[];
  seasonal: Anime[];
}

export interface Character {
  id: number;
  role: string;
  character: {
    name: string;
    image_url: string;
  };
}

export interface Season {
  id: number;
  name: string;
  number: number;
  episodes: Episode[];
}

export interface AnimeDetail extends Anime {
  synopsis: string;
  japanese_title?: string;
  english_title?: string;
  studio?: string;
  source?: string;
  rank?: number;
  popularity?: number;
  members?: number;
  aired_from?: string;
  banner_image?: string;
  characters: Character[];
  seasons: Season[];
  is_subscribed: boolean;
}

export interface FansubGroup {
  id: number;
  name: string;
}

export interface VideoFile {
  id: number;
  file_url?: string;
  quality: string;
  language: string;
  is_hardcoded: boolean;
  fansub_group?: FansubGroup;
  encryption_key?: string;
}

export interface ExternalSource {
  id: number;
  source_name: string;
  url: string;
  quality: string;
}

export interface EpisodeDetail extends Episode {
  video_files: VideoFile[];
  external_sources: ExternalSource[];
  video_url?: string; // Derived or direct
}

export interface Room {
  uuid: string;
  episode: EpisodeDetail;
  host_username: string;
  created_at: string;
  is_active: boolean;
  max_participants: number;
}

export const contentService = {
  getHomeData: async () => {
    const { data } = await api.get<HomeData>('/home/');
    return data;
  },
  
  getAnimeDetail: async (id: string) => {
    const { data } = await api.get<AnimeDetail>(`/anime/${id}/`);
    return data;
  },

  getEpisodeDetail: async (id: string) => {
    const { data } = await api.get<EpisodeDetail>(`/episodes/${id}/`);
    return data;
  },

  searchAnime: async (params: { search?: string; genre?: string; ordering?: string }) => {
    const { data } = await api.get('/anime/', { params });
    return data;
  },
};

export const watchPartyService = {
  createRoom: async (episodeId: number) => {
    const { data } = await api.post<Room>('/watch-parties/', {
      episode_id: episodeId,
    });
    return data;
  },

  getRoom: async (uuid: string) => {
    const { data } = await api.get<Room>(`/watch-parties/${uuid}/`);
    return data;
  },
};

export const authService = {
  login: async (credentials: any) => {
    const { data } = await axios.post('http://localhost:8000/api/token/', credentials);
    if (data.access) {
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);
    }
    return data;
  },
  
  logout: () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  },
  
  getProfile: async () => {
    const { data } = await api.get('/profile/');
    return data;
  }
};

export default api;
