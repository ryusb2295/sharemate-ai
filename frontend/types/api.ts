export type User = {
  id: number;
  email: string;
  display_name: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: 'bearer';
  user: User;
};

export type House = {
  id: number;
  name: string;
  location: string;
  invite_code: string;
  created_by: string;
  owner_id: number | null;
  created_at: string;
  member_count: number;
};

export type HouseMember = {
  id: number;
  house_id: number;
  user_id: number;
  display_name: string;
  email: string;
  role: 'owner' | 'member' | string;
  joined_at: string;
};

export type ReceiptItem = {
  name: string;
  quantity: number;
  price: number;
};

export type ReceiptAnalysis = {
  store_name: string;
  items: ReceiptItem[];
  total: number;
  analysis_mode: 'openai' | 'mock';
  warning: string | null;
};

export type Chore = {
  id: number;
  house_id: number;
  title: string;
  description: string;
  assignee_user_id: number;
  scheduled_date: string;
  is_completed: boolean;
  status: string;
  completed_at: string | null;
  created_by: number | null;
  created_at: string;
  assignee: {
    user_id: number;
    display_name: string;
  };
};
