const Calendar = () => {
  const { useState } = React;
  const [currentDate, setCurrentDate] = useState(new Date());

  const getDaysInMonth = (date) => {
      return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (date) => {
      return (new Date(date.getFullYear(), date.getMonth(), 1).getDay() + 6) % 7;
  };

  const handlePrevMonth = () => {
      setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
      setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
  };

  const renderDays = () => {
      const days = [];
      const daysInMonth = getDaysInMonth(currentDate);
      const firstDay = getFirstDayOfMonth(currentDate);

      // Add empty cells for days before the first day
      for (let i = 0; i < firstDay; i++) {
          days.push(React.createElement('div', { key: `empty-${i}`, className: 'p-2' }));
      }

      // Add the days of the month
      for (let day = 1; day <= daysInMonth; day++) {
          const dayOfWeek = (firstDay + day - 1) % 7;
          const isWeekend = dayOfWeek === 5 || dayOfWeek === 6;
          days.push(
              React.createElement(
                  'div',
                  {
                      key: day,
                      className: `p-2 text-center cursor-pointer hover:bg-teal-700 rounded-full ${
                          isWeekend ? 'text-red-400' : ''
                      }`,
                  },
                  day
              )
          );
      }

      return days;
  };

  return React.createElement(
      'div',
      { className: 'bg-teal-900 bg-opacity-20 rounded-xl p-4 m-4 backdrop-blur-sm' },
      React.createElement(
          'div',
          { className: 'flex justify-between items-center mb-4' },
          React.createElement(
              'h2',
              { className: 'text-xl font-semibold' },
              currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })
          ),
          React.createElement(
              'div',
              { className: 'space-x-2' },
              React.createElement(
                  'button',
                  {
                      onClick: handlePrevMonth,
                      className: 'px-3 py-1 rounded hover:bg-teal-700'
                  },
                  '❮'
              ),
              React.createElement(
                  'button',
                  {
                      onClick: handleNextMonth,
                      className: 'px-3 py-1 rounded hover:bg-teal-700'
                  },
                  '❯'
              )
          )
      ),
      React.createElement(
          'div',
          { className: 'grid grid-cols-7 gap-1' },
          React.createElement('div', { className: 'text-center font-bold' }, 'Mon'),
          React.createElement('div', { className: 'text-center font-bold' }, 'Tue'),
          React.createElement('div', { className: 'text-center font-bold' }, 'Wed'),
          React.createElement('div', { className: 'text-center font-bold' }, 'Thu'),
          React.createElement('div', { className: 'text-center font-bold' }, 'Fri'),
          React.createElement('div', { className: 'text-center font-bold text-red-400' }, 'Sat'),
          React.createElement('div', { className: 'text-center font-bold text-red-400' }, 'Sun'),
          ...renderDays()
      )
  );
};

// Export the Calendar component
window.Calendar = Calendar;


// const Calendar = () => {
//   const { useState } = React;
//   const [currentDate, setCurrentDate] = useState(new Date());

//   const getDaysInMonth = (date) => {
//     return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
//   };

//   const getFirstDayOfMonth = (date) => {
//     // Adjust so that Monday is 0 and Sunday is 6
//     return (new Date(date.getFullYear(), date.getMonth(), 1).getDay() + 6) % 7;
//   };

//   const handlePrevMonth = () => {
//     setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() - 1, 1));
//   };

//   const handleNextMonth = () => {
//     setCurrentDate((prev) => new Date(prev.getFullYear(), prev.getMonth() + 1, 1));
//   };

//   const renderDays = () => {
//     const days = [];
//     const daysInMonth = getDaysInMonth(currentDate);
//     const firstDay = getFirstDayOfMonth(currentDate);

//     // Add empty cells for days before the first day
//     for (let i = 0; i < firstDay; i++) {
//       days.push(React.createElement('div', { key: `empty-${i}`, className: 'p-2' }));
//     }

//     // Add the days of the month
//     for (let day = 1; day <= daysInMonth; day++) {
//       // Saturday = 5, Sunday = 6 based on adjusted firstDay
//       const dayOfWeek = (firstDay + day - 1) % 7;
//       const isWeekend = dayOfWeek === 5 || dayOfWeek === 6;
//       days.push(
//         React.createElement(
//           'div',
//           {
//             key: day,
//             className: `p-2 text-center cursor-pointer hover:bg-teal-700 rounded-full ${
//               isWeekend ? 'text-red-400' : ''
//             }`,
//           },
//           day
//         )
//       );
//     }

//     return days;
//   };

//   return React.createElement(
//     'div',
//     { className: 'bg-teal-900 bg-opacity-20 rounded-xl p-4 m-4 backdrop-blur-sm' },
//     React.createElement(
//       'div',
//       { className: 'flex justify-between items-center mb-4' },
//       React.createElement(
//         'h2',
//         { className: 'text-xl font-semibold' },
//         currentDate.toLocaleString('default', { month: 'long', year: 'numeric' })
//       ),
//       React.createElement(
//         'div',
//         { className: 'space-x-2' },
//         React.createElement(
//           'button',
//           { onClick: handlePrevMonth, className: 'px-3 py-1 rounded hover:bg-teal-700' },
//           '❮'
//         ),
//         React.createElement(
//           'button',
//           { onClick: handleNextMonth, className: 'px-3 py-1 rounded hover:bg-teal-700' },
//           '❯'
//         )
//       )
//     ),
//     React.createElement(
//       'div',
//       { className: 'grid grid-cols-7 gap-1' },
//       React.createElement('div', { className: 'text-center font-bold' }, 'Mon'),
//       React.createElement('div', { className: 'text-center font-bold' }, 'Tue'),
//       React.createElement('div', { className: 'text-center font-bold' }, 'Wed'),
//       React.createElement('div', { className: 'text-center font-bold' }, 'Thu'),
//       React.createElement('div', { className: 'text-center font-bold' }, 'Fri'),
//       React.createElement('div', { className: 'text-center font-bold text-red-400' }, 'Sat'),
//       React.createElement('div', { className: 'text-center font-bold text-red-400' }, 'Sun'),
//       ...renderDays()
//     )
//   );
// };

// // Export the Calendar component
// window.Calendar = Calendar;
