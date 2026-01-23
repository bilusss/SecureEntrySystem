import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { employeesApi, authApi, entriesApi } from '../services/api';

const AdminDashboard = () => {
  const [employees, setEmployees] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showQrModal, setShowQrModal] = useState(false);
  const [qrImageUrl, setQrImageUrl] = useState(null);
  const [editingEmployee, setEditingEmployee] = useState(null);
  const [newEmployee, setNewEmployee] = useState({ firstName: '', lastName: '', email: '', photo: null });
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);
  const navigate = useNavigate();

  // Sprawdzenie autoryzacji
  useEffect(() => {
    const loggedIn = localStorage.getItem('adminLoggedIn');
    if (!loggedIn) {
      navigate('/admin');
      return;
    }
    loadEmployees();
  }, [navigate]);

  const loadEmployees = async () => {
    setIsLoading(true);
    setError('');
    try {
      const data = await employeesApi.list();
      setEmployees(data || []);
    } catch (err) {
      console.error('Błąd ładowania pracowników:', err);
      setError(err.message || 'Nie udało się załadować listy pracowników');
      if (err.message?.includes('401') || err.message?.includes('Unauthorized')) {
        localStorage.removeItem('adminLoggedIn');
        navigate('/admin');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteEmployee = async (employeeId) => {
    if (!confirm('Czy na pewno chcesz usunąć tego pracownika?')) return;
    
    try {
      await employeesApi.delete(employeeId);
      setEmployees(employees.filter(e => e.id !== employeeId));
      setSuccessMessage('Pracownik został usunięty');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Błąd usuwania pracownika:', err);
      setError(err.message || 'Nie udało się usunąć pracownika');
    }
  };

  const handleAddEmployee = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!newEmployee.photo) {
      setError('Zdjęcie pracownika jest wymagane');
      return;
    }

    try {
      const created = await employeesApi.create(
        {
          email: newEmployee.email,
          firstName: newEmployee.firstName,
          lastName: newEmployee.lastName,
        },
        newEmployee.photo
      );
      setEmployees([...employees, created]);
      setShowAddModal(false);
      setNewEmployee({ firstName: '', lastName: '', email: '', photo: null });
      setSuccessMessage('Pracownik został dodany');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Błąd dodawania pracownika:', err);
      setError(err.message || 'Nie udało się dodać pracownika');
    }
  };

  const handleEditEmployee = async (e) => {
    e.preventDefault();
    setError('');

    try {
      const updated = await employeesApi.update(
        editingEmployee.id,
        {
          email: editingEmployee.email,
          firstName: editingEmployee.first_name,
          lastName: editingEmployee.last_name,
        },
        editingEmployee.newPhoto || null
      );
      setEmployees(employees.map(e => e.id === updated.id ? updated : e));
      setShowEditModal(false);
      setEditingEmployee(null);
      setSuccessMessage('Dane pracownika zostały zaktualizowane');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Błąd aktualizacji pracownika:', err);
      setError(err.message || 'Nie udało się zaktualizować danych pracownika');
    }
  };

  const handleGenerateQrCode = async (employeeId) => {
    try {
      const qrBlob = await employeesApi.generateQrCode(employeeId);
      const qrUrl = URL.createObjectURL(qrBlob);
      setQrImageUrl(qrUrl);
      setShowQrModal(true);
      setSuccessMessage('Kod QR został wygenerowany');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Błąd generowania kodu QR:', err);
      setError(err.message || 'Nie udało się wygenerować kodu QR');
    }
  };

  const handleRevokeQrCode = async (employeeId) => {
    if (!confirm('Czy na pewno chcesz unieważnić kod QR tego pracownika?')) return;
    
    try {
      await employeesApi.revokeQrCode(employeeId);
      setSuccessMessage('Kod QR został unieważniony');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (err) {
      console.error('Błąd unieważniania kodu QR:', err);
      setError(err.message || 'Nie udało się unieważnić kodu QR');
    }
  };

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch (err) {
      console.error('Błąd wylogowania:', err);
    }
    localStorage.removeItem('adminLoggedIn');
    localStorage.removeItem('adminUser');
    navigate('/admin');
  };

  const handleGenerateReport = async () => {
    setIsGeneratingReport(true);
    setError('');
    try {
      const result = await entriesApi.generateReport();
      setSuccessMessage(`${result.message}`);
      setTimeout(() => setSuccessMessage(''), 5000);
    } catch (err) {
      console.error('Błąd generowania raportu:', err);
      setError(err.message || 'Nie udało się wygenerować raportu');
    } finally {
      setIsGeneratingReport(false);
    }
  };

  const openEditModal = (employee) => {
    setEditingEmployee({ ...employee, newPhoto: null });
    setShowEditModal(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      {/* Header */}
      <header className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link to="/" className="text-2xl font-bold text-emerald-400">
              🔐 SecureEntrySystem
            </Link>
            <span className="text-slate-400">|</span>
            <span className="text-slate-300">Panel Admina</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">
              Zalogowany: <span className="text-emerald-400">{localStorage.getItem('adminUser')}</span>
            </span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded-lg transition-colors text-sm"
            >
              Wyloguj
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Messages */}
        {error && (
          <div className="mb-6 bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg">
            {error}
            <button onClick={() => setError('')} className="float-right">✕</button>
          </div>
        )}
        {successMessage && (
          <div className="mb-6 bg-emerald-500/10 border border-emerald-500/50 text-emerald-400 px-4 py-3 rounded-lg">
            {successMessage}
          </div>
        )}

        {/* Action Bar */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">Zarządzanie pracownikami</h1>
          <div className="flex gap-3">
            <button
              onClick={handleGenerateReport}
              disabled={isGeneratingReport}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-purple-600/50 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2"
            >
              {isGeneratingReport ? (
                <>
                  <span className="animate-spin">⏳</span> Generowanie...
                </>
              ) : (
                <>
                  📊 Generuj raport
                </>
              )}
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors flex items-center gap-2"
            >
              ➕ Dodaj pracownika
            </button>
          </div>
        </div>

        {/* Employees Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-4 border-emerald-400 border-t-transparent"></div>
          </div>
        ) : employees.length === 0 ? (
          <div className="text-center py-20 text-slate-400">
            <p className="text-xl mb-2">Brak pracowników w bazie danych</p>
            <p className="text-sm">Kliknij "Dodaj pracownika" aby dodać pierwszego</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {employees.map(employee => (
              <div
                key={employee.id}
                className="bg-slate-800 rounded-xl overflow-hidden border border-slate-700 hover:border-emerald-500/50 transition-colors group"
              >
                {/* Photo */}
                <div className="aspect-square bg-slate-700 flex items-center justify-center overflow-hidden">
                  {employee.photo_path ? (
                    <img
                      src={employeesApi.getPhotoUrl(employee.photo_path)}
                      alt={`${employee.first_name} ${employee.last_name}`}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.src = `https://api.dicebear.com/7.x/avataaars/svg?seed=${employee.first_name}`;
                      }}
                    />
                  ) : (
                    <img
                      src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${employee.first_name}`}
                      alt={`${employee.first_name} ${employee.last_name}`}
                      className="w-full h-full object-cover"
                    />
                  )}
                </div>
                
                {/* Info */}
                <div className="p-4">
                  <h3 className="font-semibold text-lg">
                    {employee.first_name} {employee.last_name}
                  </h3>
                  <p className="text-sm text-slate-400">{employee.email}</p>
                  <p className="text-xs text-slate-500 mb-4">ID: {employee.id}</p>
                  
                  {/* Actions */}
                  <div className="space-y-2">
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleGenerateQrCode(employee.id)}
                        className="flex-1 py-2 bg-blue-600/20 hover:bg-blue-600/40 text-blue-400 rounded-lg transition-colors text-sm"
                        title="Wygeneruj nowy kod QR"
                      >
                        📱 QR
                      </button>
                      <button
                        onClick={() => handleRevokeQrCode(employee.id)}
                        className="flex-1 py-2 bg-yellow-600/20 hover:bg-yellow-600/40 text-yellow-400 rounded-lg transition-colors text-sm"
                        title="Unieważnij kod QR"
                      >
                        🚫 Cofnij QR
                      </button>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEditModal(employee)}
                        className="flex-1 py-2 bg-slate-600/50 hover:bg-slate-600 text-slate-300 rounded-lg transition-colors text-sm"
                      >
                        ✏️ Edytuj
                      </button>
                      <button
                        onClick={() => handleDeleteEmployee(employee.id)}
                        className="flex-1 py-2 bg-red-600/20 hover:bg-red-600/40 text-red-400 rounded-lg transition-colors text-sm"
                      >
                        🗑️ Usuń
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Add Employee Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md border border-slate-700 shadow-2xl">
            <h2 className="text-xl font-bold mb-6">Dodaj nowego pracownika</h2>
            
            {error && (
              <div className="mb-4 bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}
            
            <form onSubmit={handleAddEmployee} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email *
                </label>
                <input
                  type="email"
                  value={newEmployee.email}
                  onChange={(e) => setNewEmployee({...newEmployee, email: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="jan.kowalski@firma.pl"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Imię *
                </label>
                <input
                  type="text"
                  value={newEmployee.firstName}
                  onChange={(e) => setNewEmployee({...newEmployee, firstName: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="Jan"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Nazwisko *
                </label>
                <input
                  type="text"
                  value={newEmployee.lastName}
                  onChange={(e) => setNewEmployee({...newEmployee, lastName: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="Kowalski"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Zdjęcie twarzy *
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setNewEmployee({...newEmployee, photo: e.target.files[0]})}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-emerald-600 file:text-white file:cursor-pointer"
                  required
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddModal(false);
                    setError('');
                  }}
                  className="flex-1 py-3 bg-slate-600 hover:bg-slate-500 rounded-lg transition-colors"
                >
                  Anuluj
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors"
                >
                  Dodaj
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Employee Modal */}
      {showEditModal && editingEmployee && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-2xl p-6 w-full max-w-md border border-slate-700 shadow-2xl">
            <h2 className="text-xl font-bold mb-6">Edytuj pracownika</h2>
            
            {error && (
              <div className="mb-4 bg-red-500/10 border border-red-500/50 text-red-400 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}
            
            <form onSubmit={handleEditEmployee} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={editingEmployee.email}
                  onChange={(e) => setEditingEmployee({...editingEmployee, email: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Imię
                </label>
                <input
                  type="text"
                  value={editingEmployee.first_name}
                  onChange={(e) => setEditingEmployee({...editingEmployee, first_name: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Nazwisko
                </label>
                <input
                  type="text"
                  value={editingEmployee.last_name}
                  onChange={(e) => setEditingEmployee({...editingEmployee, last_name: e.target.value})}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Nowe zdjęcie (opcjonalne)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setEditingEmployee({...editingEmployee, newPhoto: e.target.files[0]})}
                  className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-emerald-600 file:text-white file:cursor-pointer"
                />
              </div>
              
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingEmployee(null);
                    setError('');
                  }}
                  className="flex-1 py-3 bg-slate-600 hover:bg-slate-500 rounded-lg transition-colors"
                >
                  Anuluj
                </button>
                <button
                  type="submit"
                  className="flex-1 py-3 bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors"
                >
                  Zapisz
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* QR Code Modal */}
      {showQrModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-lg p-8 max-w-md w-full">
            <h2 className="text-xl font-bold mb-4 text-emerald-400">Kod QR</h2>
            {qrImageUrl && (
              <div className="flex justify-center mb-6">
                <img src={qrImageUrl} alt="QR Code" className="w-64 h-64" />
              </div>
            )}
            <p className="text-slate-300 text-sm mb-4">
              Wyświetl ten kod QR pracownikowi. Może go zeskanować przy wejściu na teren fabryki.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => {
                  if (qrImageUrl) {
                    const a = document.createElement('a');
                    a.href = qrImageUrl;
                    a.download = 'qrcode.png';
                    a.click();
                  }
                }}
                className="flex-1 py-2 bg-emerald-600 hover:bg-emerald-700 rounded-lg transition-colors"
              >
                ⬇️ Pobierz
              </button>
              <button
                onClick={() => {
                  setShowQrModal(false);
                  setQrImageUrl(null);
                }}
                className="flex-1 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg transition-colors"
              >
                Zamknij
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;
