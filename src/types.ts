export interface Todo {
  id: number;
  title: string;
  created_at: string;
}

export interface Health {
  status: string;
  version: string;
  db_time: string;
  todos: number;
}
