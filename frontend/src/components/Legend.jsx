const ITEMS = [
  { label: 'Concert', color: 'bg-purple-500' },
  { label: 'Sports', color: 'bg-blue-500' },
  { label: 'Festival', color: 'bg-green-500' },
];

export default function Legend() {
  return (
    <div className="absolute bottom-8 left-4 z-10 bg-white rounded-2xl shadow-lg p-4 space-y-2">
      <h2 className="font-semibold text-gray-800 text-sm">Legend</h2>
      {ITEMS.map((item) => (
        <div key={item.label} className="flex items-center gap-2 text-sm text-gray-600">
          <div className={`w-3 h-3 rounded-full ${item.color}`} />
          {item.label}
        </div>
      ))}
    </div>
  );
}