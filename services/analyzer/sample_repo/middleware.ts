export function middleware(request) {
  const url = request.nextUrl.clone();
  return NextResponse.next();
}
