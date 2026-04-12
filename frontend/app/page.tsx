import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="max-w-2xl w-full text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          NGO Resource Platform
        </h1>
        <p className="text-lg text-gray-600 mb-12">
          Connecting people in crisis to the nearest NGO with available resources — instantly.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* User side */}
          <div className="bg-white rounded-2xl border border-gray-200 p-8">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-red-600 text-xl">🆘</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Need Help?
            </h2>
            <p className="text-gray-500 text-sm mb-6">
              Submit a help request and we will match you with the nearest NGO that has resources available.
            </p>
            <Link
              href="/request"
              className="block w-full bg-red-500 text-white py-3 rounded-xl text-center font-medium hover:bg-red-600 transition"
            >
              Request Help
            </Link>
          </div>

          {/* NGO side */}
          <div className="bg-white rounded-2xl border border-gray-200 p-8">
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-green-600 text-xl">🏥</span>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              NGO Login
            </h2>
            <p className="text-gray-500 text-sm mb-6">
              Access your dashboard to manage resources, view incoming requests, and dispatch aid.
            </p>
            <Link
              href="/login"
              className="block w-full bg-green-600 text-white py-3 rounded-xl text-center font-medium hover:bg-green-700 transition"
            >
              NGO Dashboard
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}