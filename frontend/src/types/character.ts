export interface PersonalityTraits {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
}

export interface Character {
  id: string;
  name: string;
  description: string;
  avatar_url?: string;
  personality_traits?: PersonalityTraits;
  ecosystem_id?: string;
  autonomy_level: number;
  social_energy: number;
  is_public: boolean;
  is_active: boolean;
  interaction_count: number;
  created_at: string;
  updated_at: string;
  current_context?: Record<string, any>;
}

export interface Relationship {
  id: string;
  character_a_id: string;
  character_b_id: string;
  relationship_type: 'close_friend' | 'friend' | 'acquaintance' | 'neutral' | 'rival' | 'enemy';
  strength: number; // -1 to 1
  trust: number; // 0 to 1
  familiarity: number; // 0 to 1
  interaction_count: number;
  last_interaction?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface CharacterInteraction {
  id?: string;
  ecosystem_id: string;
  interaction_type: string;
  participants: Array<{
    id: string;
    name: string;
    role: 'initiator' | 'responder';
  }>;
  content?: string;
  response?: string;
  relationship_change?: {
    strength_delta: number;
    trust_delta: number;
    new_strength: number;
    new_trust: number;
    familiarity_delta?: number;
    new_familiarity?: number;
  };
  emotional_states?: Record<string, Record<string, number>>;
  sentiment?: number;
  timestamp: string;
}

export interface Ecosystem {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  settings: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InteractionRequest {
  initiator_id: string;
  target_id: string;
  interaction_type: string;
  content: string;
  context?: Record<string, any>;
}

export interface InteractionResponse {
  success: boolean;
  response?: string;
  relationship_change?: Record<string, number>;
  emotional_state?: Record<string, number>;
  reason?: string;
  metadata?: Record<string, any>;
}