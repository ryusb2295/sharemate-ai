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
  member_count: number;
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
  title: string;
  due_date: string;
  status: string;
  assignee: {
    user_id: number | null;
    display_name: string;
  };
};
