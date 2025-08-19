import React, { useEffect, useState } from 'react';
import { listAllUsers } from '../../utils/api';
import '../../styles/QueryHistory.css';

interface UserListProps {
  onUserSelect: (userId: string) => void;
  selectedUserId: string | null;
}

interface UserItem {
  user_id: string;
  email: string;
  is_admin: boolean;
  created_at: string;
}

const UserList: React.FC<UserListProps> = ({ onUserSelect, selectedUserId }) => {
  const [users, setUsers] = useState<UserItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadUsers = async () => {
      setLoading(true);
      try {
        const response = await listAllUsers();
        setUsers(response.users);
      } catch (error) {
        console.error('Failed to load users:', error);
        setUsers([]);
      } finally {
        setLoading(false);
      }
    };

    loadUsers();
  }, []);

  return (
    <div className="history-sidebar">
      <h3>All Users</h3>
      {loading ? (
        <div className="loading">Loading...</div>
      ) : (
        <div className="query-list">
          {users.map((user) => (
            <div
              key={user.user_id}
              className={`history-item ${selectedUserId === user.user_id ? 'selected' : ''}`}
              onClick={() => onUserSelect(user.user_id)}
            >
              <div className="history-date">
                {new Date(user.created_at).toLocaleDateString()}
                {user.is_admin && <span style={{ color: '#e74c3c', marginLeft: '8px' }}>Admin</span>}
              </div>
              <div className="history-question">{user.email}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default UserList;
